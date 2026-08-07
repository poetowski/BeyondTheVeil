from datetime import datetime, timezone

from app.models.veil_run import VeilRun


def is_visible(run: VeilRun, *, now: datetime | None = None) -> bool:
    """A run's result_payload may only be shown once its duration has elapsed."""
    now = now or datetime.now(timezone.utc)
    return now >= run.resolves_at
