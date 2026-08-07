# BeyondTheVeil

An asynchronous browser game. Each player controls one hero (strength,
dexterity, intelligence, vitality, agility, spirit) equipped across six slots
(weapon, helmet, shield, armor, amulet, spell skill). Entering the veil — a
portal that generates a fresh "reality fragment" each time — sends the hero
into a PvE encounter; results are revealed once the run's timer elapses.

- `backend/` — FastAPI + PostgreSQL (SQLAlchemy + Alembic). See
  `backend/README.md` for setup.
- `frontend/` — React + Vite + TypeScript: login/signup and an authenticated
  shell (Hero / The Veil / Concept). See `frontend/README.md` for setup.
