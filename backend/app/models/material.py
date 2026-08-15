import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.crafting import CraftingCategory, crafting_category_enum


class MaterialTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "material_templates"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[CraftingCategory] = mapped_column(
        crafting_category_enum, nullable=False, default=CraftingCategory.ALCHEMY
    )
    # See ItemTemplate.price for the buy/sell-price convention and the
    # default=0 rationale.
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    material_instances: Mapped[list["MaterialInstance"]] = relationship(back_populates="template")


class MaterialInstance(UUIDPKMixin, Base):
    __tablename__ = "material_instances"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_gt_0"),)

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_templates.id"), nullable=False
    )
    owner_hero_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_veil_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("veil_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    acquired_at: Mapped[datetime] = mapped_column(server_default=func.now())

    template: Mapped["MaterialTemplate"] = relationship(back_populates="material_instances")
    owner_hero: Mapped["Hero | None"] = relationship(
        back_populates="material_instances", foreign_keys=[owner_hero_id]
    )
    source_veil_run: Mapped["VeilRun | None"] = relationship(foreign_keys=[source_veil_run_id])
