"""rename forge materials to be more grounded/natural

Revision ID: d169c39e07bb
Revises: 716db68b96ef
Create Date: 2026-08-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd169c39e07bb'
down_revision: Union[str, Sequence[str], None] = '716db68b96ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (old_slug, new_name, new_slug, new_description, new_price)
RENAMES = [
    (
        'starsteel-ingot', 'Steelhide', 'steelhide',
        'Hide boiled and pressed until it holds an edge like steel.', 190,
    ),
    (
        'voidglass-shard', 'Soul Part', 'soul-part',
        'A small, cold weight left behind after something stopped being alive.', 180,
    ),
    (
        'phoenix-ash', 'Silver Ore', 'silver-ore',
        "Raw ore, veined with silver before anyone's touched it.", 170,
    ),
]


def upgrade() -> None:
    """The three Forge materials added last turn (Starsteel Ingot/Voidglass
    Shard/Phoenix Ash) read as too mid-or-endgame exotic - renamed to
    grounded, natural equivalents while keeping the same level_requirement
    (10) and row identity (renamed in place by slug, not deleted/
    reinserted, matching the Boar rename precedent). Idempotent - a no-op
    once already renamed, since the WHERE clause won't match anymore."""
    for old_slug, name, new_slug, description, price in RENAMES:
        op.execute(
            f"UPDATE material_templates SET name = '{name}', slug = '{new_slug}', "
            f"description = '{description.replace(chr(39), chr(39)+chr(39))}', price = {price} "
            f"WHERE slug = '{old_slug}'"
        )


def downgrade() -> None:
    """No-op - reverting a rename isn't meaningful once new art/content may
    reference the new names."""
    pass
