"""set health elixir level requirement to 15

Revision ID: 2081a2a02cc3
Revises: d169c39e07bb
Create Date: 2026-08-16 06:00:56.781888

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2081a2a02cc3'
down_revision: Union[str, Sequence[str], None] = 'd169c39e07bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Health Elixir and its recipe were seeded at level_requirement=10 -
    seed_dev_data.py's insert-only seed() will never update those rows on
    an already-seeded database. Idempotent - a no-op once already 15."""
    op.execute(
        "UPDATE consumable_templates SET level_requirement = 15 "
        "WHERE slug = 'health-elixir' AND level_requirement = 10"
    )
    op.execute(
        "UPDATE crafting_recipes SET level_requirement = 15 "
        "WHERE slug = 'health-elixir-veilbloom-blend' AND level_requirement = 10"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE consumable_templates SET level_requirement = 10 "
        "WHERE slug = 'health-elixir' AND level_requirement = 15"
    )
    op.execute(
        "UPDATE crafting_recipes SET level_requirement = 10 "
        "WHERE slug = 'health-elixir-veilbloom-blend' AND level_requirement = 15"
    )
