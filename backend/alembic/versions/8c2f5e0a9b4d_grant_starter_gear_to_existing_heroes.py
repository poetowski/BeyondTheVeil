"""grant starter gear to existing heroes

Revision ID: 8c2f5e0a9b4d
Revises: 2081a2a02cc3
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8c2f5e0a9b4d'
down_revision: Union[str, Sequence[str], None] = '2081a2a02cc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mirrors hero_service.STARTER_GEAR_SLUGS - kept as a literal here (not
# imported) since migrations must stay stable even if that constant changes
# later. (slug, equipment_slot) pairs.
STARTER_GEAR = [
    ("wooden-stick", "weapon"),
    ("wooden-shield", "shield"),
    ("leather-helm", "helmet"),
    ("leather-robe", "armor"),
]


def upgrade() -> None:
    """Backfills the tier-1 starter kit onto every hero who doesn't already
    have something equipped in that slot.

    New heroes get this automatically at signup (see
    hero_service.grant_starter_gear), but that only covers heroes created
    after this change shipped - every hero already sitting in a deployed
    database, unarmed and unarmored from character creation, needs this
    one-time backfill to actually receive it. Only fills empty slots, never
    replaces gear a hero already equipped - idempotent and safe to re-run.
    """
    for slug, slot in STARTER_GEAR:
        op.execute(
            f"""
            INSERT INTO item_instances (id, template_id, owner_hero_id, equipped_slot)
            SELECT gen_random_uuid(), t.id, h.id, '{slot}'
            FROM heroes h
            CROSS JOIN item_templates t
            WHERE t.slug = '{slug}'
              AND NOT EXISTS (
                  SELECT 1 FROM item_instances existing
                  WHERE existing.owner_hero_id = h.id
                    AND existing.equipped_slot = '{slot}'
              )
            """
        )


def downgrade() -> None:
    """No-op - removing gear a hero may have since built on top of
    (runes fused, or simply been playing with equipped) isn't meaningful,
    same spirit as this repo's other one-time content backfills."""
    pass
