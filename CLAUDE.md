# Beyond the Veil — Agent Instructions

## Verification

- **Backend-only changes**: verify with tests and direct checks (pytest, `curl`/API calls, `alembic check`) and report the results — no screenshot needed.
- **Frontend or any browser-visible change** (once `frontend/` exists): launch the app, exercise the change in a real browser (Chromium is pre-installed; see the `run` skill), take a screenshot of the result, and show it to the user (e.g. via `SendUserFile`) alongside a description of what changed. Do this every time such a change is tested — not just on request.
