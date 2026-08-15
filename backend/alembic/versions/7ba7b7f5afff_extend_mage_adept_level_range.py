"""extend mage adept level range to 10-12

Revision ID: 7ba7b7f5afff
Revises: fc27a9a61da1
Create Date: 2026-08-15 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7ba7b7f5afff'
down_revision: Union[str, Sequence[str], None] = 'fc27a9a61da1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mage Adept's level_range_max was seeded as 10 in an earlier
    migration/deploy - seed_dev_data.py's insert-only seed() will never
    update that row on an already-seeded database. Idempotent - a no-op
    once level_range_max is already 12."""
    op.execute(
        "UPDATE monster_templates SET level_range_max = 12 "
        "WHERE slug = 'mage-adept' AND level_range_max = 10"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE monster_templates SET level_range_max = 10 "
        "WHERE slug = 'mage-adept' AND level_range_max = 12"
    )
