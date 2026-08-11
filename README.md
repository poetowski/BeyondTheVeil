# Beyond the Veil

An asynchronous browser game. Somewhere behind the world you know, the Veil
waits — a seam in reality that never quite closes. Every time a hero steps
through, it generates a fresh "reality fragment" and sends them into a PvE
encounter; there's no map to memorize, just the decision to go in again and
see what's there this time. Results are revealed once the run's timer
elapses, so play is check-in-and-see rather than real-time.

## Gameplay

- **Hero** — one character per player, built from six stats (in this fixed
  order everywhere they appear): **strength, dexterity, intelligence,
  vitality, agility, spirit**. Equipped across six slots: weapon, helmet,
  shield, armor, amulet, spell skill.
- **The Veil** — enter to trigger a timed PvE encounter against a monster
  drawn from the **Bestiary**. Combat is deterministic and seed-reproducible:
  an opening spell exchange, then physical rounds, both sides' gear/authored
  stats (hero equipment; monster weapon attack, spell attack, and defense)
  feeding real damage and mitigation math.
- **Crafting** — gather materials from Veil encounters and turn them into
  consumables via **Alchemy** and **Forge** recipes.
- **Backpack / Materials** — inventory screens for held items and crafting
  materials.
- **Leaderboard** — see how your hero's level stacks up against others.

## Tech stack

- `backend/` — FastAPI + PostgreSQL (SQLAlchemy + Alembic), JWT auth. See
  [`backend/README.md`](backend/README.md) for setup, tests, and migrations.
- `frontend/` — React + Vite + TypeScript, plain CSS. See
  [`frontend/README.md`](frontend/README.md) for setup and structure.

## Quickstart

Run backend and frontend as two separate dev servers:

```bash
# backend (see backend/README.md for full setup)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
python -m scripts.seed_dev_data   # optional: dev item/monster content
uvicorn app.main:app --reload

# frontend, in a second terminal (see frontend/README.md for full setup)
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Deployment

`render.yaml` defines a single Render web service that builds the frontend,
then serves both the built static assets and the API from one FastAPI
process — backed by an external Neon Postgres database. See the comments in
`render.yaml` for the exact build/start commands and required environment
variables.
