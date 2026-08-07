import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class MonsterTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "monster_templates"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level_range_min: Mapped[int] = mapped_column(Integer, nullable=False)
    level_range_max: Mapped[int] = mapped_column(Integer, nullable=False)
    base_stats: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    flavor_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    loot_entries: Mapped[list["MonsterLootEntry"]] = relationship(
        back_populates="monster_template"
    )


class MonsterLootEntry(UUIDPKMixin, Base):
    __tablename__ = "monster_loot_entries"

    monster_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monster_templates.id", ondelete="CASCADE"), nullable=False
    )
    item_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("item_templates.id", ondelete="CASCADE"), nullable=False
    )
    drop_weight: Mapped[float] = mapped_column(Numeric, nullable=False)

    monster_template: Mapped["MonsterTemplate"] = relationship(back_populates="loot_entries")
