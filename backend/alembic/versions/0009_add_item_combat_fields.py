"""add item combat fields

Revision ID: d2e4a7c9f103
Revises: c1c3f2b0e7a1
Create Date: 2026-08-09 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e4a7c9f103'
down_revision: Union[str, Sequence[str], None] = 'c1c3f2b0e7a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('item_templates', sa.Column('damage_min', sa.Integer(), nullable=True))
    op.add_column('item_templates', sa.Column('damage_max', sa.Integer(), nullable=True))
    op.add_column(
        'item_templates',
        sa.Column('defense', sa.Integer(), server_default='0', nullable=False),
    )
    op.add_column(
        'item_templates',
        sa.Column('bonus_max_hp', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_check_constraint(
        op.f('ck_item_templates_damage_range_valid'),
        'item_templates',
        'damage_max IS NULL OR damage_min IS NULL OR damage_max >= damage_min',
    )
    op.create_check_constraint(
        op.f('ck_item_templates_defense_non_negative'), 'item_templates', 'defense >= 0'
    )
    op.create_check_constraint(
        op.f('ck_item_templates_bonus_max_hp_non_negative'), 'item_templates', 'bonus_max_hp >= 0'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_item_templates_bonus_max_hp_non_negative'), 'item_templates', type_='check')
    op.drop_constraint(op.f('ck_item_templates_defense_non_negative'), 'item_templates', type_='check')
    op.drop_constraint(op.f('ck_item_templates_damage_range_valid'), 'item_templates', type_='check')
    op.drop_column('item_templates', 'bonus_max_hp')
    op.drop_column('item_templates', 'defense')
    op.drop_column('item_templates', 'damage_max')
    op.drop_column('item_templates', 'damage_min')
