# Beyond the Veil — Agent Instructions

## Stat order

The six hero/monster stats are **always** listed, declared, and displayed in
this exact order: **strength, dexterity, intelligence, vitality, agility,
spirit**. This applies everywhere a full stat list appears or is iterated for
display/serialization — API schemas (`HeroOut` and friends), the canonical
`STAT_NAMES` tuple in `hero_service.py`, frontend stat tables/types, and the
`Hero` SQLAlchemy model's column declaration order. Follow this strictly and
persistently on every change that touches stats, not just when reminded.

## Content additions require explicit permission

Never add, invent, or propose new game content (items, monsters,
materials, consumables, recipes, campaign nodes, loot entries, flavor
text, descriptions, etc.) unless the user has explicitly asked for it in
that turn. If a task seems to call for new content but none was given,
stop and ask what the content should be rather than filling it in
yourself. This applies even when the surrounding task is otherwise
clearly scoped (e.g. "add the mechanic for X" does not imply permission
to also invent sample content for X).

## Verification

- **Backend-only changes**: verify with tests and direct checks (pytest, `curl`/API calls, `alembic check`) and report the results — no screenshot needed.
- **Frontend or any browser-visible change** (once `frontend/` exists): launch the app, exercise the change in a real browser (Chromium is pre-installed; see the `run` skill), take a screenshot of the result, and show it to the user (e.g. via `SendUserFile`) alongside a description of what changed. Do this every time such a change is tested — not just on request.
