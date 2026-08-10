"""remove campaign

Revision ID: 47570e97aeed
Revises: 8e4f94869796
Create Date: 2026-08-10 17:09:08.527413

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '47570e97aeed'
down_revision: Union[str, Sequence[str], None] = '8e4f94869796'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Removes the Campaign feature entirely: campaign_nodes and
    campaign_chapters tables, heroes.campaign_progress, and the
    veil_runs.campaign_node_id FK that pinned a run to a campaign node.

    Order matters for FK dependencies: veil_runs.campaign_node_id (which
    references campaign_nodes) is dropped first, then campaign_nodes (which
    references campaign_chapters via chapter_id), then campaign_chapters.
    """
    op.drop_constraint(op.f('fk_veil_runs_campaign_node_id_campaign_nodes'), 'veil_runs', type_='foreignkey')
    op.drop_column('veil_runs', 'campaign_node_id')
    op.drop_table('campaign_nodes')
    op.drop_table('campaign_chapters')
    op.drop_constraint(op.f('ck_heroes_campaign_progress_gte_0'), 'heroes', type_='check')
    op.drop_column('heroes', 'campaign_progress')


def downgrade() -> None:
    """No-op - recreating a deliberately-removed feature's empty schema
    isn't meaningful (matches the precedent set by 0015)."""
    pass
