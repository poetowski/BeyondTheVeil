import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class MonsterTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "monster_templates"
    __table_args__ = (
        CheckConstraint("no_drop_weight >= 0", name="no_drop_weight_non_negative"),
        CheckConstraint("no_material_drop_weight >= 0", name="no_material_drop_weight_non_negative"),
        CheckConstraint("gold_min >= 0", name="gold_min_non_negative"),
        CheckConstraint("gold_max >= gold_min", name="gold_max_gte_gold_min"),
        CheckConstraint("weapon_attack_min >= 0", name="weapon_attack_min_non_negative"),
        CheckConstraint("weapon_attack_max >= weapon_attack_min", name="weapon_attack_max_gte_min"),
        CheckConstraint("defense >= 0", name="defense_non_negative"),
        CheckConstraint("spell_attack_min >= 0", name="spell_attack_min_non_negative"),
        CheckConstraint("spell_attack_max >= spell_attack_min", name="spell_attack_max_gte_min"),
    )

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level_range_min: Mapped[int] = mapped_column(Integer, nullable=False)
    level_range_max: Mapped[int] = mapped_column(Integer, nullable=False)
    base_stats: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    flavor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Weighted alongside each MonsterLootEntry's drop_weight in the item-loot
    # roll (see combat/engine.py) - lets "drops nothing" odds vary per
    # monster instead of a fixed global chance. 0 means always drops
    # something when it has a loot pool at all.
    no_drop_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Same idea as no_drop_weight, but for the material-loot roll.
    no_material_drop_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gold_min: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    gold_max: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    # Flat, non-item combat numbers - unlike hero gear, monsters have no
    # equipment to derive these from. weapon_attack adds a roll on top of
    # strength's flat physical-damage contribution (see engine.py);
    # spell_attack does the same on top of intelligence's flat spell-damage
    # contribution; defense flat-reduces physical damage the monster takes
    # (unzoned, since monsters have no equipment slots to split it across).
    weapon_attack_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weapon_attack_max: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defense: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spell_attack_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spell_attack_max: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    loot_entries: Mapped[list["MonsterLootEntry"]] = relationship(
        back_populates="monster_template"
    )
    material_loot_entries: Mapped[list["MonsterMaterialLootEntry"]] = relationship(
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


class MonsterMaterialLootEntry(UUIDPKMixin, Base):
    __tablename__ = "monster_material_loot_entries"

    monster_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monster_templates.id", ondelete="CASCADE"), nullable=False
    )
    material_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_templates.id", ondelete="CASCADE"), nullable=False
    )
    drop_weight: Mapped[float] = mapped_column(Numeric, nullable=False)

    monster_template: Mapped["MonsterTemplate"] = relationship(
        back_populates="material_loot_entries"
    )
