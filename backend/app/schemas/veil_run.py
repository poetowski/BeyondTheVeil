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
    loot_skipped: list[dict] = []
    material_loot: list[dict] = []
    xp_awarded: int
    gold_awarded: int = 0


class VeilEncounterOut(BaseModel):
    """Who the hero is fighting - unlike VeilRunResultOut, this is never
    time-gated: knowing your opponent doesn't spoil the outcome, so a combat
    screen can show it for the whole countdown, not just after resolves_at.
    """

    monster_name: str | None = None
    monster_stats: dict[str, int] | None = None
    monster_max_hp: int | None = None


class VeilRunOut(BaseModel):
    id: uuid.UUID
    status: VeilRunStatus
    started_at: datetime
    resolves_at: datetime
    encounter: VeilEncounterOut | None
    result: VeilRunResultOut | None


def to_out(run: VeilRun, *, now: datetime | None = None) -> VeilRunOut:
    """Builds the API-facing view of a run: `result` is populated whenever
    `is_visible()` is true, independent of `status` — a run's outcome can be
    seen before it's explicitly claimed, since revealing (time-gated) and
    claiming (applying XP/loot) are separate concerns by design. `encounter`
    is populated as soon as the payload exists, regardless of visibility.
    """
    payload = run.result_payload
    encounter = None
    if payload is not None:
        encounter = VeilEncounterOut(
            monster_name=payload.get("monster_name"),
            monster_stats=payload.get("monster_stats"),
            monster_max_hp=payload.get("monster_max_hp"),
        )
    result = None
    if payload is not None and is_visible(run, now=now):
        result = VeilRunResultOut(**payload)
    return VeilRunOut(
        id=run.id,
        status=run.status,
        started_at=run.started_at,
        resolves_at=run.resolves_at,
        encounter=encounter,
        result=result,
    )
