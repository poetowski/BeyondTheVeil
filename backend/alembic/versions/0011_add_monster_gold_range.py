"""add monster gold_min/gold_max

Revision ID: f7a9c2d3e405
Revises: e5f6a8b1c204
Create Date: 2026-08-09 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7a9c2d3e405'
down_revision: Union[str, Sequence[str], None] = 'e5f6a8b1c204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'monster_templates',
        sa.Column('gold_min', sa.Integer(), server_default='10', nullable=False),
    )
    op.add_column(
        'monster_templates',
        sa.Column('gold_max', sa.Integer(), server_default='10', nullable=False),
    )
    op.create_check_constraint(
        op.f('ck_monster_templates_gold_min_non_negative'),
        'monster_templates',
        'gold_min >= 0',
    )
    op.create_check_constraint(
        op.f('ck_monster_templates_gold_max_gte_gold_min'),
        'monster_templates',
        'gold_max >= gold_min',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_monster_templates_gold_max_gte_gold_min'), 'monster_templates', type_='check')
    op.drop_constraint(op.f('ck_monster_templates_gold_min_non_negative'), 'monster_templates', type_='check')
    op.drop_column('monster_templates', 'gold_max')
    op.drop_column('monster_templates', 'gold_min')
