import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class CampaignNode(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "campaign_nodes"
    __table_args__ = (
        CheckConstraint("order_index > 0", name="order_index_gt_0"),
        CheckConstraint("required_level >= 1", name="required_level_gte_1"),
        CheckConstraint("gold_cost >= 0", name="gold_cost_gte_0"),
    )

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    gold_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monster_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monster_templates.id", ondelete="RESTRICT"), nullable=False
    )

    monster_template: Mapped["MonsterTemplate"] = relationship()
