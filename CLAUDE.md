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

## New content always ships with art in the same change

Any new item, monster, material, consumable, or rune that has an art
skill (`bestiary-art`, `material-art`, `item-art`) must get its art drawn
as part of the same change that adds it — never leave a newly-added
piece of content without art, even if that turn's request didn't
separately say "and draw art for it." Naming the content is enough
permission for its art too (the art skills' own "only draw what's been
explicitly named" rule is satisfied by the content request itself).
Finish the content, then immediately invoke the matching art skill
before considering the task done.

## Changes to already-shipped content must ship as a data migration

`backend/scripts/seed_dev_data.py` only inserts rows that are missing (it
checks `slug` and skips if the row already exists) — editing a dict in
that file does **nothing** to a database that was already seeded. This
means a rename, value tweak, or removal made only in that file affects
brand-new installs only; every already-seeded database (including
production) keeps the old content forever unless something else updates it.

Likewise, running ad-hoc `psql`/SQL directly against a local or sandbox
database is **not a fix** — it only patches that one local database, not
the real deployed one, and creates the false impression the change is
"done" when it never shipped anywhere real.

The only mechanism that reaches the real database is an Alembic migration,
because `alembic upgrade head` runs automatically on every deploy (see
`render.yaml`'s `startCommand`). So: whenever you rename, edit, or delete
content that may already exist in a seeded database — an item, monster,
material, recipe, rune, stat, weight, description, or any other seeded
field — write a migration that performs the change with `op.execute(...)`
(`UPDATE`/`DELETE`, guarded by `WHERE slug = '<old_value>'` so it's a safe
no-op if already applied), in addition to updating `seed_dev_data.py` for
fresh installs. See `alembic/versions/0015_remove_wisp_dummy_data.py`,
`0020_remove_threshold_buckler_dummy_data.py`, and
`7fa372c21c3b_add_shop.py` (price backfill) for the established pattern.
Never consider a content change to already-shipped data "done" without one.

## Verification

- **Backend-only changes**: verify with tests and direct checks (pytest, `curl`/API calls, `alembic check`) and report the results — no screenshot needed.
- **Frontend or any browser-visible change** (once `frontend/` exists): launch the app, exercise the change in a real browser (Chromium is pre-installed; see the `run` skill), take a screenshot of the result, and show it to the user (e.g. via `SendUserFile`) alongside a description of what changed. Do this every time such a change is tested — not just on request.
