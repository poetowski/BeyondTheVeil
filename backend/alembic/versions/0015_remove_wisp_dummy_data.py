"""remove wisp dummy data

Revision ID: 43c09fa4859f
Revises: c3d4e5f6a708
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '43c09fa4859f'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a708'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Delete leftover Veil Wisp / Minor Healing Elixir dummy content.

    This content was removed from scripts/seed_dev_data.py in commits
    7f232b8/bb596ba/f246e87, but that script only inserts missing rows -
    it never deletes ones already committed to a database seeded before
    those commits. Deletes are slug-targeted and idempotent (no-op if the
    rows are already absent), and ordered to satisfy FK constraints
    (campaign_nodes -> monster_templates and crafting_recipes ->
    consumable_templates are RESTRICT, not CASCADE). The consumable/item/
    material/monster deletes are additionally guarded with NOT EXISTS
    checks against anything that might still reference them, so this can
    never fail a deploy by hitting a FK violation - it just leaves a row
    in place if something unexpected still points at it.
    """
    op.execute(
        "DELETE FROM campaign_nodes "
        "WHERE slug IN ('campaign-01-wisp-threshold', 'campaign-02-wisp-hollow')"
    )
    op.execute(
        "DELETE FROM monster_loot_entries "
        "WHERE monster_template_id IN (SELECT id FROM monster_templates WHERE slug = 'veil-wisp')"
    )
    op.execute(
        "DELETE FROM monster_material_loot_entries "
        "WHERE monster_template_id IN (SELECT id FROM monster_templates WHERE slug = 'veil-wisp')"
    )
    op.execute(
        "DELETE FROM crafting_recipe_ingredients "
        "WHERE recipe_id IN (SELECT id FROM crafting_recipes WHERE slug = 'minor-healing-elixir')"
    )
    op.execute("DELETE FROM crafting_recipes WHERE slug = 'minor-healing-elixir'")
    op.execute(
        "DELETE FROM consumable_templates "
        "WHERE slug = 'minor-healing-elixir' "
        "AND NOT EXISTS (SELECT 1 FROM consumable_instances WHERE template_id = consumable_templates.id)"
    )
    op.execute(
        "DELETE FROM item_templates "
        "WHERE slug = 'wisp-spark' "
        "AND NOT EXISTS (SELECT 1 FROM item_instances WHERE template_id = item_templates.id)"
    )
    op.execute(
        "DELETE FROM material_templates "
        "WHERE slug = 'wisp-residue' "
        "AND NOT EXISTS (SELECT 1 FROM crafting_recipe_ingredients WHERE material_template_id = material_templates.id) "
        "AND NOT EXISTS (SELECT 1 FROM monster_material_loot_entries WHERE material_template_id = material_templates.id)"
    )
    op.execute(
        "DELETE FROM monster_templates "
        "WHERE slug = 'veil-wisp' "
        "AND NOT EXISTS (SELECT 1 FROM campaign_nodes WHERE monster_template_id = monster_templates.id)"
    )


def downgrade() -> None:
    """No-op - recreating deliberately-removed dummy content isn't meaningful."""
    pass
