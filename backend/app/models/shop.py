import uuid
from datetime import date as date_
from datetime import datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPKMixin


class ShopPurchase(UUIDPKMixin, Base):
    """One row per (hero, calendar date, slot) purchase - the unique
    constraint below is the actual once-per-slot-per-day guarantee;
    shop_service's pre-check is only there for a friendlier error message.
    Deliberately has no relationships - always queried directly by
    hero_id/shop_date/slot_index (see shop_service), same style as
    hero_service.get_owned_*."""

    __tablename__ = "shop_purchases"
    __table_args__ = (
        UniqueConstraint("hero_id", "shop_date", "slot_index", name="uq_shop_purchases_hero_date_slot"),
        CheckConstraint(
            "(item_template_id IS NULL) != (material_template_id IS NULL)",
            name="exactly_one_target",
        ),
        CheckConstraint("slot_index >= 0 AND slot_index < 6", name="slot_index_in_range"),
        CheckConstraint("price_paid >= 0", name="price_paid_non_negative"),
    )

    hero_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=False
    )
    shop_date: Mapped[date_] = mapped_column(Date, nullable=False)
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    item_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("item_templates.id"), nullable=True
    )
    material_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_templates.id"), nullable=True
    )
    price_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(server_default=func.now())
