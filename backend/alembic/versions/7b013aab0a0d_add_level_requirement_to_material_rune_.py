"""add level_requirement to material/rune/consumable templates

Revision ID: 7b013aab0a0d
Revises: f994686286b0
Create Date: 2026-08-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7b013aab0a0d'
down_revision: Union[str, Sequence[str], None] = 'f994686286b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the same organizational level_requirement field ItemTemplate
    already has to MaterialTemplate, RuneTemplate, and ConsumableTemplate.
    The column default (1) is correct for every row except two, which are
    corrected below by slug - Nettle only drops from level 4+ monsters, and
    Greater Healing Potion's recipes are level_requirement=5."""
    op.add_column(
        'material_templates',
        sa.Column('level_requirement', sa.Integer(), server_default='1', nullable=False),
    )
    op.add_column(
        'rune_templates',
        sa.Column('level_requirement', sa.Integer(), server_default='1', nullable=False),
    )
    op.add_column(
        'consumable_templates',
        sa.Column('level_requirement', sa.Integer(), server_default='1', nullable=False),
    )
    op.execute(
        "UPDATE material_templates SET level_requirement = 4 WHERE slug = 'nettle'"
    )
    op.execute(
        "UPDATE consumable_templates SET level_requirement = 5 WHERE slug = 'greater-healing-potion'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('consumable_templates', 'level_requirement')
    op.drop_column('rune_templates', 'level_requirement')
    op.drop_column('material_templates', 'level_requirement')
