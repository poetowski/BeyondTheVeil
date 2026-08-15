"""fix seed content drift

Revision ID: a773a82a3b4c
Revises: 7fa372c21c3b
Create Date: 2026-08-15 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a773a82a3b4c'
down_revision: Union[str, Sequence[str], None] = '7fa372c21c3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply content edits that were only ever made to scripts/seed_dev_data.py.

    That script inserts a row if its slug is missing and otherwise skips it
    - it never updates a row that's already there. So every rename/value
    tweak made to it this session (commits 0bd8ce5, fad00a3, 5b114ea,
    1107dfb) only took effect on brand-new installs; any database seeded
    before those commits still has the old content.

    Worse: because seed_dev_data.py runs on every deploy (render.yaml), a
    database that was already seeded under the OLD slug got a second,
    duplicate row inserted under the NEW slug on the first deploy after
    each rename commit landed (before this migration existed to fix the
    old row in place) - it looked for the new slug, didn't find it, and
    inserted fresh. So a target database may have: only the old row, only
    the new row, or both. Each block below handles all three by merging
    into the old row's id when a duplicate new-slug row exists (repointing
    any live references first, since rune_templates is referenced by
    player-owned rune_instances/item_instances), then renaming that row to
    the new slug/name. Every statement is idempotent - safe to run again
    on an already-fixed database.
    """
    # --- Ironhide Boar -> Boar (1107dfb) ---
    # monster_templates has no external references besides its own loot
    # entries (both ondelete=CASCADE), so a duplicate 'boar' row can just
    # be dropped outright before the old row is renamed onto that slug.
    op.execute("DELETE FROM monster_templates WHERE slug = 'boar' "
               "AND EXISTS (SELECT 1 FROM monster_templates WHERE slug = 'ironhide-boar')")
    op.execute(
        "UPDATE monster_templates SET slug = 'boar', name = 'Boar' "
        "WHERE slug = 'ironhide-boar'"
    )

    # --- Rune of Vigor -> Vrelka Rune of Vigor (fad00a3) ---
    _merge_rune(old_slug="rune-of-vigor", new_slug="vrelka-rune-of-vigor")
    op.execute(
        "UPDATE rune_templates SET slug = 'vrelka-rune-of-vigor', name = 'Vrelka Rune of Vigor' "
        "WHERE slug = 'rune-of-vigor'"
    )
    _merge_recipe(old_slug="rune-of-vigor", new_slug="vrelka-rune-of-vigor")
    op.execute(
        "UPDATE crafting_recipes SET slug = 'vrelka-rune-of-vigor', name = 'Vrelka Rune of Vigor' "
        "WHERE slug = 'rune-of-vigor'"
    )

    # --- Rune of Might -> Vosk Rune of Might, azure-rework description (fad00a3, 5b114ea) ---
    _merge_rune(old_slug="rune-of-might", new_slug="vosk-rune-of-might")
    op.execute(
        "UPDATE rune_templates SET slug = 'vosk-rune-of-might', name = 'Vosk Rune of Might', "
        "description = 'Three azure shards radiating around a glowing core.' "
        "WHERE slug = 'rune-of-might'"
    )
    _merge_recipe(old_slug="rune-of-might", new_slug="vosk-rune-of-might")
    op.execute(
        "UPDATE crafting_recipes SET slug = 'vosk-rune-of-might', name = 'Vosk Rune of Might' "
        "WHERE slug = 'rune-of-might'"
    )

    # --- Veil Wisp's Ember Dust drop weight 8 -> 33 (0bd8ce5) ---
    # No duplicate-row risk here: the (monster, material) pair already
    # existed before the weight-bump commit, so seed_dev_data.py's
    # exists-check always skipped re-inserting it.
    op.execute(
        "UPDATE monster_material_loot_entries SET drop_weight = 33 "
        "WHERE drop_weight = 8 "
        "AND monster_template_id = (SELECT id FROM monster_templates WHERE slug = 'veil-wisp') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'ember-dust')"
    )


def _merge_rune(old_slug: str, new_slug: str) -> None:
    """If both an old-slug and new-slug rune_templates row exist, repoint every
    live reference to the duplicate new row onto the old row's id, then drop
    the now-unreferenced duplicate. No-op if only one (or neither) exists."""
    op.execute(f"""
        DO $$
        DECLARE
            old_id uuid;
            new_id uuid;
        BEGIN
            SELECT id INTO old_id FROM rune_templates WHERE slug = '{old_slug}';
            SELECT id INTO new_id FROM rune_templates WHERE slug = '{new_slug}';
            IF old_id IS NOT NULL AND new_id IS NOT NULL AND old_id != new_id THEN
                UPDATE rune_instances SET template_id = old_id WHERE template_id = new_id;
                UPDATE item_instances SET rune_template_id = old_id WHERE rune_template_id = new_id;
                UPDATE crafting_recipes SET output_rune_template_id = old_id WHERE output_rune_template_id = new_id;
                DELETE FROM rune_templates WHERE id = new_id;
            END IF;
        END $$;
    """)


def _merge_recipe(old_slug: str, new_slug: str) -> None:
    """If both an old-slug and new-slug crafting_recipes row exist, drop the
    duplicate new row (its ingredients cascade-delete; nothing else
    references a recipe row). No-op if only one (or neither) exists."""
    op.execute(
        f"DELETE FROM crafting_recipes WHERE slug = '{new_slug}' "
        f"AND EXISTS (SELECT 1 FROM crafting_recipes WHERE slug = '{old_slug}')"
    )


def downgrade() -> None:
    """No-op - reverting to withdrawn names/values isn't meaningful."""
    pass
