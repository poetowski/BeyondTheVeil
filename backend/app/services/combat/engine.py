import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CombatResult:
    victory: bool
    log: list[dict[str, Any]] = field(default_factory=list)
    loot: list[dict[str, Any]] = field(default_factory=list)
    xp_awarded: int = 0


def resolve(seed: int, hero_snapshot: dict[str, int], encounter: dict[str, Any]) -> CombatResult:
    """Deterministic interface stub for the combat resolver.

    Full hit-chance / damage / magic formulas are a separate future task —
    this only guarantees a deterministic, seed-reproducible CombatResult so
    the veil-run lifecycle (enter -> resolve -> claim) can be built and
    tested end to end ahead of the real combat math.
    """
    rng = random.Random(seed)
    victory = rng.random() < 0.5
    return CombatResult(
        victory=victory,
        log=[{"message": "combat engine stub: outcome decided by seed"}],
        loot=[],
        xp_awarded=10 if victory else 0,
    )
