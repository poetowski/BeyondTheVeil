"""lower iron helm defense

Revision ID: 1f6efe36171c
Revises: a773a82a3b4c
Create Date: 2026-08-15 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1f6efe36171c'
down_revision: Union[str, Sequence[str], None] = 'a773a82a3b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Iron Helm's defense was tuned down from 5 to 4 right after it shipped
    (seed_dev_data.py only inserts missing rows, so this must reach any
    database that already ran the seed with the old value). Idempotent -
    a no-op if already at 4."""
    op.execute(
        "UPDATE item_templates SET defense = 4 WHERE slug = 'iron-helm' AND defense = 5"
    )


def downgrade() -> None:
    """No-op - reverting a balance tweak isn't meaningful."""
    pass
