"""shorten flower kid unlock_hint

Revision ID: a4c7e2f0b8d1
Revises: f1a6c8d3e9b2
Create Date: 2026-08-16 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a4c7e2f0b8d1'
down_revision: Union[str, Sequence[str], None] = 'f1a6c8d3e9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """seed_dev_data.py only inserts missing rows, so editing its
    unlock_hint string there does nothing for a database that already has
    the Flower Kid Avatar row - see CLAUDE.md. The original text ("Craft a
    Herbalist Hell potion in Alchemy (level 15) and drink it.") made that
    avatar card noticeably wider than the other five in the picker's
    flex-wrap grid, breaking the 3-per-row layout - this shorter text
    fixes that. Slug-targeted and idempotent."""
    op.execute(
        "UPDATE avatar_templates SET unlock_hint = 'Drink a Herbalist Hell.' "
        "WHERE slug = 'flower-kid-avatar'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE avatar_templates SET unlock_hint = "
        "'Craft a Herbalist Hell potion in Alchemy (level 15) and drink it.' "
        "WHERE slug = 'flower-kid-avatar'"
    )
