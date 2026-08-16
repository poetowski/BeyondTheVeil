import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class AvatarTemplate(UUIDPKMixin, TimestampMixin, Base):
    """A selectable hero portrait, unlocked one of three ways (see
    hero_service.is_avatar_unlocked):
    - price>0: a one-time gold purchase, recorded as a HeroAvatarUnlock row
      (see hero_service.unlock_avatar).
    - price=0, unlock_hint=None: automatically unlocked once hero.level
      reaches level_requirement - no purchase, no row, just a level check.
    - price=0, unlock_hint set: gated behind a specific in-game action
      (e.g. consuming a particular consumable - see
      crafting_service.use_consumable's Herbalist Hell special case)
      rather than gold or level alone; also recorded as a HeroAvatarUnlock
      row, granted by whatever code path performs that action (see
      hero_service.grant_avatar_unlock), not the purchase endpoint - price
      being 0 keeps the purchase endpoint from ever selling it directly
      (see unlock_avatar's price==0 guard).
    A price=0/level_requirement=1/unlock_hint=None avatar (Peasant Avatar)
    is unlocked for everyone from the start."""

    __tablename__ = "avatar_templates"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Same organizational field ItemTemplate/MaterialTemplate use, but here
    # it also gates unlocking (see is_avatar_unlocked) rather than just
    # being informational.
    level_requirement: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Display order in the picker - not alphabetical, so Peasant (the free
    # starter) always leads regardless of what gets added later.
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Non-null only for a price=0 avatar that's gated behind a specific
    # action rather than reaching level_requirement alone (see the class
    # docstring's third case) - doubles as both the "this isn't just
    # free-at-level" signal for is_avatar_unlocked and the locked-card
    # copy shown to the player (see schemas/avatar.py's AvatarTemplateOut
    # and the frontend's AvatarPage).
    unlock_hint: Mapped[str | None] = mapped_column(Text, nullable=True)


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
