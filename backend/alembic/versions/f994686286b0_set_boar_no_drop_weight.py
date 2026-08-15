"""set boar no_drop_weight

Revision ID: f994686286b0
Revises: 1f6efe36171c
Create Date: 2026-08-15 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f994686286b0'
down_revision: Union[str, Sequence[str], None] = '1f6efe36171c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Boar just gained an item loot table (see seed_dev_data.py) after
    previously having none, so its no_drop_weight (left at the column
    default of 0, meaning "always drops something") needs to move to 40 to
    match the other item-dropping monsters. Boar already exists in any
    seeded database, so seed_dev_data.py's insert-only seed() would never
    touch this column on its own. Idempotent - only fires while still at
    the old default."""
    op.execute(
        "UPDATE monster_templates SET no_drop_weight = 40 WHERE slug = 'boar' AND no_drop_weight = 0"
    )


def downgrade() -> None:
    """No-op - reverting a balance tweak isn't meaningful."""
    pass
