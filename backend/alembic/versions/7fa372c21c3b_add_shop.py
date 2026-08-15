"""add shop

Revision ID: 7fa372c21c3b
Revises: 98df2eb569cb
Create Date: 2026-08-15 09:49:50.903660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa372c21c3b'
down_revision: Union[str, Sequence[str], None] = '98df2eb569cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Backfill for rows that predate this migration (fresh installs get these
# via seed_dev_data.py instead - this is what makes an already-deployed DB
# agree with a freshly seeded one). Any slug not listed here (custom
# content added directly to a deployed DB) falls back to 1, distinct from
# a deliberate 0/free price - go back and price it for real.
ITEM_PRICES = {
    'wooden-stick': 140,
    'wooden-shield': 175,
    'leather-helm': 126,
    'leather-robe': 84,
    'old-ring': 315,
}
MATERIAL_PRICES = {
    'plantago': 28,
    'chamomile': 21,
    'iron-ore': 35,
    'tin-shard': 42,
    'ember-dust': 56,
}
CONSUMABLE_PRICES = {
    'minor-healing-potion': 210,
}
RUNE_PRICES = {
    'vrelka-rune-of-vigor': 1540,
    'vosk-rune-of-might': 1540,
}


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('shop_purchases',
    sa.Column('hero_id', sa.UUID(), nullable=False),
    sa.Column('shop_date', sa.Date(), nullable=False),
    sa.Column('slot_index', sa.Integer(), nullable=False),
    sa.Column('item_template_id', sa.UUID(), nullable=True),
    sa.Column('material_template_id', sa.UUID(), nullable=True),
    sa.Column('price_paid', sa.Integer(), nullable=False),
    sa.Column('purchased_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.CheckConstraint('(item_template_id IS NULL) != (material_template_id IS NULL)', name=op.f('ck_shop_purchases_exactly_one_target')),
    sa.CheckConstraint('price_paid >= 0', name=op.f('ck_shop_purchases_price_paid_non_negative')),
    sa.CheckConstraint('slot_index >= 0 AND slot_index < 6', name=op.f('ck_shop_purchases_slot_index_in_range')),
    sa.ForeignKeyConstraint(['hero_id'], ['heroes.id'], name=op.f('fk_shop_purchases_hero_id_heroes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_template_id'], ['item_templates.id'], name=op.f('fk_shop_purchases_item_template_id_item_templates')),
    sa.ForeignKeyConstraint(['material_template_id'], ['material_templates.id'], name=op.f('fk_shop_purchases_material_template_id_material_templates')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_shop_purchases')),
    sa.UniqueConstraint('hero_id', 'shop_date', 'slot_index', name='uq_shop_purchases_hero_date_slot')
    )

    # price columns: added nullable, backfilled by slug, then locked to
    # NOT NULL - can't add a NOT NULL column with no default to a table
    # that already has rows.
    op.add_column('item_templates', sa.Column('price', sa.Integer(), nullable=True))
    op.add_column('material_templates', sa.Column('price', sa.Integer(), nullable=True))
    op.add_column('consumable_templates', sa.Column('price', sa.Integer(), nullable=True))
    op.add_column('rune_templates', sa.Column('price', sa.Integer(), nullable=True))

    for slug, price in ITEM_PRICES.items():
        op.execute(f"UPDATE item_templates SET price = {price} WHERE slug = '{slug}'")
    op.execute("UPDATE item_templates SET price = 1 WHERE price IS NULL")

    for slug, price in MATERIAL_PRICES.items():
        op.execute(f"UPDATE material_templates SET price = {price} WHERE slug = '{slug}'")
    op.execute("UPDATE material_templates SET price = 1 WHERE price IS NULL")

    for slug, price in CONSUMABLE_PRICES.items():
        op.execute(f"UPDATE consumable_templates SET price = {price} WHERE slug = '{slug}'")
    op.execute("UPDATE consumable_templates SET price = 1 WHERE price IS NULL")

    for slug, price in RUNE_PRICES.items():
        op.execute(f"UPDATE rune_templates SET price = {price} WHERE slug = '{slug}'")
    op.execute("UPDATE rune_templates SET price = 1 WHERE price IS NULL")

    op.alter_column('item_templates', 'price', existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(op.f('ck_item_templates_price_non_negative'), 'item_templates', 'price >= 0')
    op.alter_column('material_templates', 'price', existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(op.f('ck_material_templates_price_non_negative'), 'material_templates', 'price >= 0')
    op.alter_column('consumable_templates', 'price', existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(op.f('ck_consumable_templates_price_non_negative'), 'consumable_templates', 'price >= 0')
    op.alter_column('rune_templates', 'price', existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(op.f('ck_rune_templates_price_non_negative'), 'rune_templates', 'price >= 0')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_rune_templates_price_non_negative'), 'rune_templates', type_='check')
    op.drop_column('rune_templates', 'price')
    op.drop_constraint(op.f('ck_consumable_templates_price_non_negative'), 'consumable_templates', type_='check')
    op.drop_column('consumable_templates', 'price')
    op.drop_constraint(op.f('ck_material_templates_price_non_negative'), 'material_templates', type_='check')
    op.drop_column('material_templates', 'price')
    op.drop_constraint(op.f('ck_item_templates_price_non_negative'), 'item_templates', type_='check')
    op.drop_column('item_templates', 'price')
    op.drop_table('shop_purchases')
