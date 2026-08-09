"""add material category

Revision ID: c1c3f2b0e7a1
Revises: a6618679f668
Create Date: 2026-08-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1c3f2b0e7a1'
down_revision: Union[str, Sequence[str], None] = 'a6618679f668'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # crafting_category enum type already exists (created in 0007) - reuse it,
    # don't recreate.
    op.add_column(
        'material_templates',
        sa.Column(
            'category',
            sa.Enum('alchemy', 'forge', name='crafting_category', create_type=False),
            server_default='alchemy',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('material_templates', 'category')
