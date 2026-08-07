from datetime import timedelta

from app.schemas.veil_run import is_visible
from app.services import veil_service


def test_resolves_at_matches_started_at_plus_duration(db_session, hero_factory):
    hero = hero_factory()

    run = veil_service.enter_veil(db_session, hero)

    assert run.resolves_at == run.started_at + timedelta(seconds=run.duration_seconds)


def test_result_is_hidden_until_resolves_at_then_visible(db_session, hero_factory):
    hero = hero_factory()
    run = veil_service.enter_veil(db_session, hero)

    assert run.result_payload is not None, "result is computed immediately"
    assert not is_visible(run, now=run.started_at), "must stay hidden before resolves_at"
    assert is_visible(run, now=run.resolves_at), "must become visible once resolves_at passes"
