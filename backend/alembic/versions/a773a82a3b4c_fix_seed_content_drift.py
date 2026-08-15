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
    before those commits still has the old content. Each UPDATE below is
    slug-targeted and idempotent (no-op if the row is already at its new
    value, e.g. on a database seeded after those commits).
    """
    # Ironhide Boar -> Boar (1107dfb)
    op.execute(
        "UPDATE monster_templates SET slug = 'boar', name = 'Boar' "
        "WHERE slug = 'ironhide-boar'"
    )

    # Rune of Vigor -> Vrelka Rune of Vigor (fad00a3)
    op.execute(
        "UPDATE rune_templates SET slug = 'vrelka-rune-of-vigor', name = 'Vrelka Rune of Vigor' "
        "WHERE slug = 'rune-of-vigor'"
    )
    op.execute(
        "UPDATE crafting_recipes SET slug = 'vrelka-rune-of-vigor', name = 'Vrelka Rune of Vigor' "
        "WHERE slug = 'rune-of-vigor'"
    )

    # Rune of Might -> Vosk Rune of Might, plus its azure-rework description (fad00a3, 5b114ea)
    op.execute(
        "UPDATE rune_templates SET slug = 'vosk-rune-of-might', name = 'Vosk Rune of Might', "
        "description = 'Three azure shards radiating around a glowing core.' "
        "WHERE slug = 'rune-of-might'"
    )
    op.execute(
        "UPDATE crafting_recipes SET slug = 'vosk-rune-of-might', name = 'Vosk Rune of Might' "
        "WHERE slug = 'rune-of-might'"
    )

    # Veil Wisp's Ember Dust drop weight 8 -> 33 (0bd8ce5)
    op.execute(
        "UPDATE monster_material_loot_entries SET drop_weight = 33 "
        "WHERE drop_weight = 8 "
        "AND monster_template_id = (SELECT id FROM monster_templates WHERE slug = 'veil-wisp') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'ember-dust')"
    )


def downgrade() -> None:
    """No-op - reverting to withdrawn names/values isn't meaningful."""
    pass
