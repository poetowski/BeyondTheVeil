import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class RuneTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "rune_templates"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Flat stat bonuses, same shape as ItemTemplate.base_stats - folded into
    # hero_service.compute_stat_bonuses whenever the rune's host item is
    # equipped (see item_instances.rune_template_id).
    stat_bonuses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # See ItemTemplate.price for the buy/sell-price convention and the
    # default=0 rationale.
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rune_instances: Mapped[list["RuneInstance"]] = relationship(back_populates="template")


class RuneInstance(UUIDPKMixin, Base):
    __tablename__ = "rune_instances"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_gt_0"),)

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rune_templates.id"), nullable=False
    )
    owner_hero_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    acquired_at: Mapped[datetime] = mapped_column(server_default=func.now())

    template: Mapped["RuneTemplate"] = relationship(back_populates="rune_instances")
    owner_hero: Mapped["Hero | None"] = relationship(foreign_keys=[owner_hero_id])
