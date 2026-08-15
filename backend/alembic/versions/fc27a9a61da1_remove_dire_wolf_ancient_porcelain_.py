"""remove dire wolf ancient porcelain drop

Revision ID: fc27a9a61da1
Revises: cd12adc18c8f
Create Date: 2026-08-15 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fc27a9a61da1'
down_revision: Union[str, Sequence[str], None] = 'cd12adc18c8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Dire Wolf no longer drops Ancient Porcelain (Robber and Awakened
    Bear still do) - this loot entry just shipped in the previous commit,
    so seed_dev_data.py's insert-only seed() would never remove it from an
    already-seeded database. Idempotent - a no-op if already removed."""
    op.execute(
        "DELETE FROM monster_material_loot_entries "
        "WHERE monster_template_id = (SELECT id FROM monster_templates WHERE slug = 'dire-wolf') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'ancient-porcelain')"
    )


def downgrade() -> None:
    """No-op - reverting a loot-table tweak isn't meaningful."""
    pass
