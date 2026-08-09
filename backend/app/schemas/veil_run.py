import uuid
from datetime import datetime, timezone

from pydantic import BaseModel

from app.models.veil_run import VeilRun, VeilRunStatus


def is_visible(run: VeilRun, *, now: datetime | None = None) -> bool:
    """A run's result_payload may only be shown once its duration has elapsed."""
    now = now or datetime.now(timezone.utc)
    return now >= run.resolves_at


class VeilRunResultOut(BaseModel):
    victory: bool
    monster_name: str | None = None
    log: list[dict]
    loot: list[dict]
    xp_awarded: int
    gold_awarded: int = 0


class VeilRunOut(BaseModel):
    id: uuid.UUID
    status: VeilRunStatus
    started_at: datetime
    resolves_at: datetime
    result: VeilRunResultOut | None


def to_out(run: VeilRun, *, now: datetime | None = None) -> VeilRunOut:
    """Builds the API-facing view of a run: `result` is populated whenever
    `is_visible()` is true, independent of `status` — a run's outcome can be
    seen before it's explicitly claimed, since revealing (time-gated) and
    claiming (applying XP/loot) are separate concerns by design.
    """
    result = None
    if run.result_payload is not None and is_visible(run, now=now):
        result = VeilRunResultOut(**run.result_payload)
    return VeilRunOut(
        id=run.id,
        status=run.status,
        started_at=run.started_at,
        resolves_at=run.resolves_at,
        result=result,
    )
