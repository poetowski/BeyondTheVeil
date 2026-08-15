import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class EquipmentSlot(str, enum.Enum):
    WEAPON = "weapon"
    HELMET = "helmet"
    SHIELD = "shield"
    ARMOR = "armor"
    AMULET = "amulet"
    SPELL_SKILL = "spell_skill"


class ItemRarity(str, enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


equipment_slot_enum = SAEnum(
    EquipmentSlot, name="equipment_slot", values_callable=lambda enum_cls: [e.value for e in enum_cls]
)
item_rarity_enum = SAEnum(
    ItemRarity, name="item_rarity", values_callable=lambda enum_cls: [e.value for e in enum_cls]
)


class ItemTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "item_templates"
    __table_args__ = (
        CheckConstraint(
            "damage_max IS NULL OR damage_min IS NULL OR damage_max >= damage_min",
            name="damage_range_valid",
        ),
        CheckConstraint(
            "spell_damage_max IS NULL OR spell_damage_min IS NULL OR spell_damage_max >= spell_damage_min",
            name="spell_damage_range_valid",
        ),
        CheckConstraint("defense >= 0", name="defense_non_negative"),
        CheckConstraint("bonus_max_hp >= 0", name="bonus_max_hp_non_negative"),
        CheckConstraint("price >= 0", name="price_non_negative"),
    )

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slot: Mapped[EquipmentSlot] = mapped_column(equipment_slot_enum, nullable=False)
    rarity: Mapped[ItemRarity] = mapped_column(
        item_rarity_enum, nullable=False, default=ItemRarity.COMMON
    )
    base_stats: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    level_requirement: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    damage_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    damage_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spell_damage_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spell_damage_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    defense: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bonus_max_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Shop gold value: full price to buy, round(price * 0.25) to sell (see
    # hero_service.SHOP_SELL_PRICE_RATIO). Defaults to 0 rather than being
    # required so pre-existing test fixtures that construct a template
    # without a price keep working - real content always gets an explicit
    # one via seed_dev_data.py.
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item_instances: Mapped[list["ItemInstance"]] = relationship(back_populates="template")


class ItemInstance(UUIDPKMixin, Base):
    __tablename__ = "item_instances"
    __table_args__ = (
        CheckConstraint(
            "equipped_slot IS NULL OR owner_hero_id IS NOT NULL",
            name="equipped_requires_owner",
        ),
        Index(
            "uq_hero_equipped_slot",
            "owner_hero_id",
            "equipped_slot",
            unique=True,
            postgresql_where="equipped_slot IS NOT NULL",
        ),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("item_templates.id"), nullable=False
    )
    owner_hero_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=True
    )
    equipped_slot: Mapped[EquipmentSlot | None] = mapped_column(
        equipment_slot_enum, nullable=True
    )
    rolled_stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_veil_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("veil_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    # A rune permanently fused to this item, if any. Set once via
    # hero_service.apply_rune and never cleared - there is no "remove rune"
    # path, enforced at the service layer rather than the DB.
    rune_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rune_templates.id"), nullable=True
    )
    acquired_at: Mapped[datetime] = mapped_column(server_default=func.now())

    template: Mapped["ItemTemplate"] = relationship(back_populates="item_instances")
    owner_hero: Mapped["Hero | None"] = relationship(
        back_populates="item_instances", foreign_keys=[owner_hero_id]
    )
    source_veil_run: Mapped["VeilRun | None"] = relationship(
        back_populates="loot_item_instances", foreign_keys=[source_veil_run_id]
    )
    rune_template: Mapped["RuneTemplate | None"] = relationship()
