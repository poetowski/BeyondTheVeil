# Frontend

Vite + React + TypeScript, plain CSS.

## Setup

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if the backend isn't on localhost:8000
npm run dev
```

Requires the backend running (see `../backend/README.md`) — the login/signup
pages call it directly.

## Structure

- `src/api/` — typed fetch client for the backend's `/api/v1` routes
- `src/auth/` — `AuthContext` (token + session state) and the `RequireAuth` route guard
- `src/layout/` — the authenticated shell: sidebar (Hero / The Veil / Concept + logout) + content area
- `src/pages/` — one component per route
