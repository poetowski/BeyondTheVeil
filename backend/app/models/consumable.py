import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class ConsumableTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "consumable_templates"
    __table_args__ = (
        CheckConstraint("heal_flat >= 0", name="heal_flat_non_negative"),
        CheckConstraint("heal_vitality_multiplier >= 0", name="heal_vitality_multiplier_non_negative"),
        CheckConstraint("price >= 0", name="price_non_negative"),
    )

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Heal on use = heal_flat + heal_vitality_multiplier * hero's effective
    # vitality, capped at max HP (see crafting_service.use_consumable).
    heal_flat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    heal_vitality_multiplier: Mapped[float] = mapped_column(
        Numeric(asdecimal=False), nullable=False, default=0
    )
    # See ItemTemplate.price for the buy/sell-price convention and the
    # default=0 rationale.
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Same organizational field as ItemTemplate.level_requirement.
    level_requirement: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

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
