"""change consumable heal formula to flat + vitality multiplier

Revision ID: a1b2c3d4e506
Revises: f7a9c2d3e405
Create Date: 2026-08-09 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e506'
down_revision: Union[str, Sequence[str], None] = 'f7a9c2d3e405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('consumable_templates', 'heal_amount_fraction')
    op.add_column(
        'consumable_templates',
        sa.Column('heal_flat', sa.Integer(), server_default='0', nullable=False),
    )
    op.add_column(
        'consumable_templates',
        sa.Column('heal_vitality_multiplier', sa.Numeric(), server_default='0', nullable=False),
    )
    op.create_check_constraint(
        op.f('ck_consumable_templates_heal_flat_non_negative'),
        'consumable_templates',
        'heal_flat >= 0',
    )
    op.create_check_constraint(
        op.f('ck_consumable_templates_heal_vitality_multiplier_non_negative'),
        'consumable_templates',
        'heal_vitality_multiplier >= 0',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f('ck_consumable_templates_heal_vitality_multiplier_non_negative'),
        'consumable_templates',
        type_='check',
    )
    op.drop_constraint(
        op.f('ck_consumable_templates_heal_flat_non_negative'), 'consumable_templates', type_='check'
    )
    op.drop_column('consumable_templates', 'heal_vitality_multiplier')
    op.drop_column('consumable_templates', 'heal_flat')
    op.add_column(
        'consumable_templates',
        sa.Column('heal_amount_fraction', sa.Numeric(), nullable=False, server_default='0.3'),
    )
