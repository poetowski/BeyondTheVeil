"""add item spell_damage_min/spell_damage_max

Revision ID: c3d4e5f6a708
Revises: b2c3d4e5f607
Create Date: 2026-08-09 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a708'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f607'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('item_templates', sa.Column('spell_damage_min', sa.Integer(), nullable=True))
    op.add_column('item_templates', sa.Column('spell_damage_max', sa.Integer(), nullable=True))
    op.create_check_constraint(
        op.f('ck_item_templates_spell_damage_range_valid'),
        'item_templates',
        'spell_damage_max IS NULL OR spell_damage_min IS NULL OR spell_damage_max >= spell_damage_min',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_item_templates_spell_damage_range_valid'), 'item_templates', type_='check')
    op.drop_column('item_templates', 'spell_damage_max')
    op.drop_column('item_templates', 'spell_damage_min')
