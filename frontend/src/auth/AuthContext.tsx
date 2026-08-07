import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { login as apiLogin, signup as apiSignup } from "../api/auth";
import { ApiError } from "../api/client";
import type { HeroOut, LoginRequest, SignupRequest, UserOut } from "../api/types";
import { getMe } from "../api/users";

const TOKEN_STORAGE_KEY = "btv_token";

interface AuthContextValue {
  token: string | null;
  user: UserOut | null;
  hero: HeroOut | null;
  loading: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  signup: (payload: SignupRequest) => Promise<void>;
  logout: () => void;
  refetch: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<UserOut | null>(null);
  const [hero, setHero] = useState<HeroOut | null>(null);
  const [loading, setLoading] = useState(true);

  const hydrate = useCallback(async (nextToken: string) => {
    const me = await getMe(nextToken);
    setUser(me.user);
    setHero(me.hero);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        await hydrate(token);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          if (!cancelled) setToken(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restoreSession();
    return () => {
      cancelled = true;
    };
    // Runs once on mount, against whatever token was persisted at load time.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyToken = useCallback(
    async (nextToken: string) => {
      localStorage.setItem(TOKEN_STORAGE_KEY, nextToken);
      setToken(nextToken);
      await hydrate(nextToken);
    },
    [hydrate],
  );

  const login = useCallback(
    async (payload: LoginRequest) => {
      const { access_token } = await apiLogin(payload);
      await applyToken(access_token);
    },
    [applyToken],
  );

  const signup = useCallback(
    async (payload: SignupRequest) => {
      const { access_token } = await apiSignup(payload);
      await applyToken(access_token);
    },
    [applyToken],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
    setHero(null);
  }, []);

  const refetch = useCallback(async () => {
    if (token) await hydrate(token);
  }, [token, hydrate]);

  return (
    <AuthContext.Provider value={{ token, user, hero, loading, login, signup, logout, refetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
