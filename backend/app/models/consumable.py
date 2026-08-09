import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class ConsumableTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "consumable_templates"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Fraction of max HP restored on use (e.g. 0.3 == 30%), not a flat
    # number - keeps potions useful at any level without per-level tiers.
    heal_amount_fraction: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)

    consumable_instances: Mapped[list["ConsumableInstance"]] = relationship(
        back_populates="template"
    )


class ConsumableInstance(UUIDPKMixin, Base):
    __tablename__ = "consumable_instances"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_gt_0"),)

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consumable_templates.id"), nullable=False
    )
    owner_hero_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    acquired_at: Mapped[datetime] = mapped_column(server_default=func.now())

    template: Mapped["ConsumableTemplate"] = relationship(back_populates="consumable_instances")
    owner_hero: Mapped["Hero | None"] = relationship(foreign_keys=[owner_hero_id])
