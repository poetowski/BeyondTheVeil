import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class AvatarTemplate(UUIDPKMixin, TimestampMixin, Base):
    """A selectable hero portrait. price=0 avatars (e.g. Peasant Avatar) are
    available to every hero from the start; price>0 avatars must be unlocked
    once via a HeroAvatarUnlock row before a hero can select them."""

    __tablename__ = "avatar_templates"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Display order in the picker - not alphabetical, so Peasant (the free
    # starter) always leads regardless of what gets added later.
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class HeroAvatarUnlock(UUIDPKMixin, TimestampMixin, Base):
    """Records that a hero has paid to unlock a price>0 avatar. No row is
    ever created for a price=0 avatar - those are implicitly unlocked for
    everyone (see hero_service.is_avatar_unlocked)."""

    __tablename__ = "hero_avatar_unlocks"
    __table_args__ = (
        UniqueConstraint("hero_id", "avatar_template_id", name="uq_hero_avatar_unlocks_hero_avatar"),
    )

    hero_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=False
    )
    avatar_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("avatar_templates.id"), nullable=False
    )

    hero: Mapped["Hero"] = relationship()
    avatar_template: Mapped["AvatarTemplate"] = relationship()
