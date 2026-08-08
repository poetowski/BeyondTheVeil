import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Hero(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "heroes"
    __table_args__ = (
        CheckConstraint("level >= 1", name="level_gte_1"),
        CheckConstraint("xp >= 0", name="xp_gte_0"),
        CheckConstraint("strength >= 0", name="strength_gte_0"),
        CheckConstraint("dexterity >= 0", name="dexterity_gte_0"),
        CheckConstraint("intelligence >= 0", name="intelligence_gte_0"),
        CheckConstraint("vitality >= 0", name="vitality_gte_0"),
        CheckConstraint("agility >= 0", name="agility_gte_0"),
        CheckConstraint("spirit >= 0", name="spirit_gte_0"),
        CheckConstraint("gold >= 0", name="gold_gte_0"),
        CheckConstraint("campaign_progress >= 0", name="campaign_progress_gte_0"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    campaign_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dexterity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vitality: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agility: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spirit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="hero")
    item_instances: Mapped[list["ItemInstance"]] = relationship(
        back_populates="owner_hero", foreign_keys="ItemInstance.owner_hero_id"
    )
    material_instances: Mapped[list["MaterialInstance"]] = relationship(
        back_populates="owner_hero", foreign_keys="MaterialInstance.owner_hero_id"
    )
    veil_runs: Mapped[list["VeilRun"]] = relationship(back_populates="hero")
