import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class VeilRunStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


veil_run_status_enum = SAEnum(
    VeilRunStatus,
    name="veil_run_status",
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
)


class VeilRun(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "veil_runs"
    __table_args__ = (
        CheckConstraint("duration_seconds > 0", name="duration_seconds_gt_0"),
        CheckConstraint("resolves_at > started_at", name="resolves_at_after_started_at"),
        Index(
            "uq_hero_one_active_run",
            "hero_id",
            unique=True,
            postgresql_where="status = 'in_progress'",
        ),
        Index("ix_veil_runs_hero_started_at", "hero_id", "started_at"),
    )

    hero_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heroes.id", ondelete="CASCADE"), nullable=False
    )
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[VeilRunStatus] = mapped_column(
        veil_run_status_enum, nullable=False, default=VeilRunStatus.IN_PROGRESS
    )
    # started_at/resolves_at are set together by veil_service.enter_veil() at row
    # creation, not via server_default/GENERATED: Postgres generated columns must be
    # IMMUTABLE, and timestamptz + interval arithmetic is only STABLE, so a DB-side
    # generated resolves_at column is not possible for a timezone-aware timestamp.
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    resolves_at: Mapped[datetime] = mapped_column(nullable=False)
    result_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    hero: Mapped["Hero"] = relationship(back_populates="veil_runs")
    loot_item_instances: Mapped[list["ItemInstance"]] = relationship(
        back_populates="source_veil_run", foreign_keys="ItemInstance.source_veil_run_id"
    )
