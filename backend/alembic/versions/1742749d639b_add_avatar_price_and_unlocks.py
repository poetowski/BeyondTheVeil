"""add avatar price, sort order, and unlocks

Revision ID: 1742749d639b
Revises: 1df83ccc9129
Create Date: 2026-08-16 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1742749d639b'
down_revision: Union[str, Sequence[str], None] = '1df83ccc9129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'hero_avatar_unlocks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('hero_id', sa.UUID(), nullable=False),
        sa.Column('avatar_template_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hero_id'], ['heroes.id'], name=op.f('fk_hero_avatar_unlocks_hero_id_heroes'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['avatar_template_id'], ['avatar_templates.id'], name=op.f('fk_hero_avatar_unlocks_avatar_template_id_avatar_templates')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_hero_avatar_unlocks')),
        sa.UniqueConstraint('hero_id', 'avatar_template_id', name='uq_hero_avatar_unlocks_hero_avatar'),
    )

    # price/sort_order: added nullable, backfilled by slug, then locked to
    # NOT NULL - same pattern as every other "add a required column to a
    # table with existing rows" migration in this repo.
    op.add_column('avatar_templates', sa.Column('price', sa.Integer(), nullable=True))
    op.add_column('avatar_templates', sa.Column('sort_order', sa.Integer(), nullable=True))
    op.execute("UPDATE avatar_templates SET price = 0, sort_order = 0 WHERE slug = 'peasant-avatar'")
    op.execute("UPDATE avatar_templates SET price = 2000, sort_order = 1 WHERE slug = 'militia-avatar'")
    # Any other avatar already added directly to a deployed DB and not
    # covered above stays free/unordered rather than crashing this migration.
    op.execute("UPDATE avatar_templates SET price = 0 WHERE price IS NULL")
    op.execute("UPDATE avatar_templates SET sort_order = 0 WHERE sort_order IS NULL")
    op.alter_column('avatar_templates', 'price', existing_type=sa.Integer(), nullable=False)
    op.alter_column('avatar_templates', 'sort_order', existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(
        op.f('ck_avatar_templates_price_non_negative'), 'avatar_templates', 'price >= 0'
    )

    # Grandfather in anyone already wearing Militia Avatar from before this
    # paywall existed - they keep it without needing to re-buy it.
    op.execute(
        "INSERT INTO hero_avatar_unlocks (id, hero_id, avatar_template_id) "
        "SELECT gen_random_uuid(), h.id, h.avatar_template_id FROM heroes h "
        "JOIN avatar_templates a ON a.id = h.avatar_template_id "
        "WHERE a.slug = 'militia-avatar'"
    )


def downgrade() -> None:
    op.drop_constraint(op.f('ck_avatar_templates_price_non_negative'), 'avatar_templates', type_='check')
    op.drop_column('avatar_templates', 'sort_order')
    op.drop_column('avatar_templates', 'price')
    op.drop_table('hero_avatar_unlocks')
