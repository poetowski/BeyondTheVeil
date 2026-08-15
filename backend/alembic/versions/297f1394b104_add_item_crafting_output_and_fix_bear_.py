"""add item crafting output and fix bear no_drop_weight

Revision ID: 297f1394b104
Revises: 7b013aab0a0d
Create Date: 2026-08-15 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '297f1394b104'
down_revision: Union[str, Sequence[str], None] = '7b013aab0a0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crafting recipes can now output an equipment item, not just a
    consumable or a rune (needed for the two new craftable Talisman
    amulets). Widens the exactly_one_output CHECK from a 2-way XOR to a
    3-way exactly-one-of-three; existing rows are unaffected since the new
    column is null for all of them, keeping the sum at 1."""
    op.add_column(
        'crafting_recipes',
        sa.Column('output_item_template_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        op.f('fk_crafting_recipes_output_item_template_id_item_templates'),
        'crafting_recipes', 'item_templates',
        ['output_item_template_id'], ['id'],
    )
    op.drop_constraint(op.f('ck_crafting_recipes_exactly_one_output'), 'crafting_recipes', type_='check')
    op.create_check_constraint(
        op.f('ck_crafting_recipes_exactly_one_output'),
        'crafting_recipes',
        "(output_consumable_template_id IS NOT NULL)::int "
        "+ (output_rune_template_id IS NOT NULL)::int "
        "+ (output_item_template_id IS NOT NULL)::int = 1",
    )

    # Awakened Bear just gained an item loot table (see seed_dev_data.py)
    # after previously having none - its no_drop_weight (left at the
    # column default of 0) needs to move to 40 to match the other
    # item-dropping monsters. Bear already exists in any seeded database,
    # so seed_dev_data.py's insert-only seed() would never touch this
    # column on its own. Idempotent - only fires while still at the old
    # default.
    op.execute(
        "UPDATE monster_templates SET no_drop_weight = 40 "
        "WHERE slug = 'awakened-bear' AND no_drop_weight = 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_crafting_recipes_exactly_one_output'), 'crafting_recipes', type_='check')
    op.create_check_constraint(
        op.f('ck_crafting_recipes_exactly_one_output'),
        'crafting_recipes',
        "(output_consumable_template_id IS NULL) != (output_rune_template_id IS NULL)",
    )
    op.drop_constraint(
        op.f('fk_crafting_recipes_output_item_template_id_item_templates'),
        'crafting_recipes', type_='foreignkey',
    )
    op.drop_column('crafting_recipes', 'output_item_template_id')
