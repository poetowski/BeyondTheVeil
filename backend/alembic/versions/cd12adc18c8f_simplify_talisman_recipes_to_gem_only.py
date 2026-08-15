"""simplify talisman recipes to gem only

Revision ID: cd12adc18c8f
Revises: 297f1394b104
Create Date: 2026-08-15 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cd12adc18c8f'
down_revision: Union[str, Sequence[str], None] = '297f1394b104'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Spirit Talisman and Agility Talisman's recipes just shipped with a
    Gem/Veil Crystal/Scrap Metal mix (4 Gem + 3 of a secondary material) -
    simplified here to Gem x9 alone before either recipe was live long
    enough to matter, since seed_dev_data.py's insert-only seed() would
    never touch an already-shipped recipe's ingredient rows. Idempotent -
    a no-op if a database was never seeded with the old ingredient mix."""
    op.execute(
        "UPDATE crafting_recipe_ingredients SET quantity_required = 9 "
        "WHERE recipe_id = (SELECT id FROM crafting_recipes WHERE slug = 'spirit-talisman') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'gem')"
    )
    op.execute(
        "DELETE FROM crafting_recipe_ingredients "
        "WHERE recipe_id = (SELECT id FROM crafting_recipes WHERE slug = 'spirit-talisman') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'veil-crystal')"
    )
    op.execute(
        "UPDATE crafting_recipe_ingredients SET quantity_required = 9 "
        "WHERE recipe_id = (SELECT id FROM crafting_recipes WHERE slug = 'agility-talisman') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'gem')"
    )
    op.execute(
        "DELETE FROM crafting_recipe_ingredients "
        "WHERE recipe_id = (SELECT id FROM crafting_recipes WHERE slug = 'agility-talisman') "
        "AND material_template_id = (SELECT id FROM material_templates WHERE slug = 'scrap-metal')"
    )


def downgrade() -> None:
    """No-op - reverting a balance tweak isn't meaningful."""
    pass
