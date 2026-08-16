"""add avatar unlock_hint

Revision ID: f1a6c8d3e9b2
Revises: 8c2f5e0a9b4d
Create Date: 2026-08-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1a6c8d3e9b2'
down_revision: Union[str, Sequence[str], None] = '8c2f5e0a9b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Nullable, no backfill needed: every existing avatar (Peasant,
    Militia, Warrior, Adept, Fat) keeps its current unlock behavior exactly
    as-is with unlock_hint left NULL - see AvatarTemplate's docstring for
    what a non-null value changes (hero_service.is_avatar_unlocked stops
    treating price=0 as automatically-free-at-level for that row)."""
    op.add_column('avatar_templates', sa.Column('unlock_hint', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('avatar_templates', 'unlock_hint')
