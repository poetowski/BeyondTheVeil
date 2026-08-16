import threading
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.avatar import AvatarTemplate
from app.models.hero import Hero
from app.models.user import User
from app.models.veil_run import VeilRun, VeilRunStatus
from app.services import hero_service, veil_service


def _make_run(hero, *, resolves_delta_seconds: int, xp_awarded: int = 42) -> VeilRun:
    now = datetime.now(timezone.utc)
    return VeilRun(
        hero_id=hero.id,
        seed=1,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=now - timedelta(seconds=10),
        duration_seconds=5,
        resolves_at=now + timedelta(seconds=resolves_delta_seconds),
        result_payload={"victory": True, "log": [], "loot": [], "xp_awarded": xp_awarded},
    )


def test_second_in_progress_run_for_same_hero_is_rejected(db_session, hero_factory):
    hero = hero_factory()
    db_session.add(_make_run(hero, resolves_delta_seconds=60))
    db_session.flush()

    db_session.add(_make_run(hero, resolves_delta_seconds=60))
    try:
        db_session.flush()
        assert False, "expected IntegrityError from uq_hero_one_active_run"
    except IntegrityError:
        db_session.rollback()


def test_enter_veil_double_submit_returns_same_run(db_session, hero_factory):
    hero = hero_factory()

    run1 = veil_service.enter_veil(db_session, hero)
    run2 = veil_service.enter_veil(db_session, hero)

    assert run1.id == run2.id


def test_claim_before_resolves_at_is_a_noop(db_session, hero_factory):
    hero = hero_factory(xp=0)
    run = _make_run(hero, resolves_delta_seconds=3600)
    db_session.add(run)
    db_session.commit()

    claimed = veil_service.claim_run(db_session, run.id, hero.id)

    assert claimed.status == VeilRunStatus.IN_PROGRESS
    assert db_session.get(Hero, hero.id).xp == 0


def test_claim_is_idempotent(db_session, hero_factory):
    hero = hero_factory(xp=0)
    run = _make_run(hero, resolves_delta_seconds=-1, xp_awarded=42)
    db_session.add(run)
    db_session.commit()

    first = veil_service.claim_run(db_session, run.id, hero.id)
    assert first.status == VeilRunStatus.COMPLETED
    assert db_session.get(Hero, hero.id).xp == 42

    second = veil_service.claim_run(db_session, run.id, hero.id)
    assert second.status == VeilRunStatus.COMPLETED
    assert db_session.get(Hero, hero.id).xp == 42, "reward must not be applied twice"


def test_claim_run_rejects_a_different_heros_id(db_session, hero_factory):
    owner = hero_factory(xp=0)
    other = hero_factory(xp=0)
    run = _make_run(owner, resolves_delta_seconds=-1, xp_awarded=42)
    db_session.add(run)
    db_session.commit()

    claimed = veil_service.claim_run(db_session, run.id, other.id)

    assert claimed.status == VeilRunStatus.IN_PROGRESS, "wrong-hero claim must be a no-op"
    assert db_session.get(Hero, owner.id).xp == 0
    assert db_session.get(Hero, other.id).xp == 0


def test_concurrent_claim_race_only_one_applies_reward(engine):
    """Two threads racing claim_run() on the same run must only credit XP once."""
    SessionFactory = sessionmaker(bind=engine, future=True)
    setup_session = SessionFactory()
    user = User(email=f"{uuid.uuid4()}@test.com", hashed_password="x")
    setup_session.add(user)
    setup_session.flush()
    avatar = setup_session.query(AvatarTemplate).filter_by(slug="peasant-avatar").one()
    hero = Hero(
        user_id=user.id,
        avatar_template_id=avatar.id,
        name="Racer",
        strength=1,
        dexterity=1,
        vitality=1,
        agility=1,
        intelligence=1,
        spirit=1,
        xp=0,
        current_hp=hero_service.compute_max_hp(1),
    )
    setup_session.add(hero)
    setup_session.flush()

    run = _make_run(hero, resolves_delta_seconds=-5, xp_awarded=42)
    setup_session.add(run)
    setup_session.commit()
    user_id, hero_id, run_id = user.id, hero.id, run.id
    setup_session.close()

    barrier = threading.Barrier(2)
    statuses = []

    def worker():
        session = SessionFactory()
        barrier.wait()
        claimed = veil_service.claim_run(session, run_id, hero_id)
        statuses.append(claimed.status)
        session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    verify_session = SessionFactory()
    try:
        hero_after = verify_session.get(Hero, hero_id)
        assert all(status == VeilRunStatus.COMPLETED for status in statuses)
        assert hero_after.xp == 42, "reward must be applied exactly once despite the race"
    finally:
        verify_session.execute(VeilRun.__table__.delete().where(VeilRun.id == run_id))
        verify_session.execute(Hero.__table__.delete().where(Hero.id == hero_id))
        verify_session.execute(User.__table__.delete().where(User.id == user_id))
        verify_session.commit()
        verify_session.close()
