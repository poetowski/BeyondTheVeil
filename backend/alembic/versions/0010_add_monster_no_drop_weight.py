"""add monster no_drop_weight

Revision ID: e5f6a8b1c204
Revises: d2e4a7c9f103
Create Date: 2026-08-09 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a8b1c204'
down_revision: Union[str, Sequence[str], None] = 'd2e4a7c9f103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'monster_templates',
        sa.Column('no_drop_weight', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_check_constraint(
        op.f('ck_monster_templates_no_drop_weight_non_negative'),
        'monster_templates',
        'no_drop_weight >= 0',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f('ck_monster_templates_no_drop_weight_non_negative'),
        'monster_templates',
        type_='check',
    )
    op.drop_column('monster_templates', 'no_drop_weight')
