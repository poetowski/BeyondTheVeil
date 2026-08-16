"""add avatar level_requirement

Revision ID: 716db68b96ef
Revises: 1742749d639b
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '716db68b96ef'
down_revision: Union[str, Sequence[str], None] = '1742749d639b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Neither existing avatar (Peasant, Militia) is level-gated - both get
    the same default (1) ItemTemplate/MaterialTemplate use for "no level
    gate"."""
    op.add_column('avatar_templates', sa.Column('level_requirement', sa.Integer(), server_default='1', nullable=False))


def downgrade() -> None:
    op.drop_column('avatar_templates', 'level_requirement')
