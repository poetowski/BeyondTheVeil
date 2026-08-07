import { apiFetch } from "./client";
import type { LoginRequest, SignupRequest, TokenResponse } from "./types";

export function signup(payload: SignupRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/v1/auth/signup", { method: "POST", body: payload });
}

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/v1/auth/login", { method: "POST", body: payload });
}
