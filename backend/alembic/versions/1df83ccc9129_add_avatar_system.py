"""add avatar system

Revision ID: 1df83ccc9129
Revises: 7ba7b7f5afff
Create Date: 2026-08-16 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1df83ccc9129'
down_revision: Union[str, Sequence[str], None] = '7ba7b7f5afff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed id for the Peasant Avatar row this migration inserts directly -
# this migration runs before seed_dev_data.py on every deploy (see
# render.yaml's startCommand), so seeding can't supply this row yet and
# every existing hero needs a valid id to backfill against right here.
PEASANT_AVATAR_ID = 'd0c5e1ff-d285-4f42-b924-cccbb29d5b35'


def upgrade() -> None:
    op.create_table(
        'avatar_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_avatar_templates')),
        sa.UniqueConstraint('slug', name=op.f('uq_avatar_templates_slug')),
    )

    op.execute(
        f"INSERT INTO avatar_templates (id, slug, name) "
        f"VALUES ('{PEASANT_AVATAR_ID}', 'peasant-avatar', 'Peasant Avatar')"
    )

    # avatar_template_id: added nullable, backfilled to Peasant Avatar for
    # every already-existing hero, then locked to NOT NULL - can't add a
    # NOT NULL column with no default to a table that already has rows
    # (same pattern as 7fa372c21c3b_add_shop.py's price columns).
    op.add_column('heroes', sa.Column('avatar_template_id', sa.UUID(), nullable=True))
    op.execute(f"UPDATE heroes SET avatar_template_id = '{PEASANT_AVATAR_ID}'")
    op.alter_column('heroes', 'avatar_template_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key(
        op.f('fk_heroes_avatar_template_id_avatar_templates'),
        'heroes', 'avatar_templates',
        ['avatar_template_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(op.f('fk_heroes_avatar_template_id_avatar_templates'), 'heroes', type_='foreignkey')
    op.drop_column('heroes', 'avatar_template_id')
    op.drop_table('avatar_templates')
