"""remove threshold buckler dummy data

Revision ID: fc50534ac3ed
Revises: e6edf0b848fb
Create Date: 2026-08-11 10:51:58.586221

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fc50534ac3ed'
down_revision: Union[str, Sequence[str], None] = 'e6edf0b848fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Delete leftover Threshold Buckler dummy content.

    This item was removed from scripts/seed_dev_data.py in commit a9a6015
    (replaced by Wooden Shield), but that script only inserts missing rows
    - it never deletes ones already committed to a database seeded before
    that commit. Unlike 0015's item_templates delete (which skips deletion
    if any item_instances still reference it), this one deletes
    item_instances unconditionally first - confirmed explicitly wanted even
    for instances already held by a hero. Deletes are slug-targeted and
    idempotent (no-op if the rows are already absent), ordered to satisfy
    FK constraints (item_instances/monster_loot_entries -> item_templates).
    """
    op.execute(
        "DELETE FROM item_instances WHERE template_id IN "
        "(SELECT id FROM item_templates WHERE slug = 'threshold-buckler')"
    )
    op.execute(
        "DELETE FROM monster_loot_entries WHERE item_template_id IN "
        "(SELECT id FROM item_templates WHERE slug = 'threshold-buckler')"
    )
    op.execute("DELETE FROM item_templates WHERE slug = 'threshold-buckler'")


def downgrade() -> None:
    """No-op - recreating deliberately-removed dummy content isn't meaningful."""
    pass
