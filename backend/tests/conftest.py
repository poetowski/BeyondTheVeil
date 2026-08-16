import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.main import app
from app.models.avatar import AvatarTemplate
from app.models.base import Base
from app.models.hero import Hero
from app.models.monster import MonsterTemplate
from app.models.user import User
from app.services import hero_service

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://beyondtheveil:beyondtheveil@localhost:5432/beyondtheveil_test",
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL, future=True)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)

    # Broad-coverage monster so any test calling enter_veil() end-to-end has an
    # eligible encounter, regardless of hero level. Inserted once, outside any
    # per-test transaction, so it persists across every test's rollback.
    with Session(bind=eng) as setup_session:
        setup_session.add(
            MonsterTemplate(
                slug="test-fixture-monster",
                name="Test Fixture Monster",
                level_range_min=1,
                level_range_max=99,
                base_stats={
                    "strength": 5,
                    "dexterity": 5,
                    "vitality": 5,
                    "agility": 5,
                    "intelligence": 5,
                    "spirit": 5,
                },
            )
        )
        # Every Hero row requires an avatar_template_id - slugged "peasant-avatar"
        # to match what app/api/v1/auth.py's signup handler looks up, so both
        # hero_factory (below) and the real signup endpoint share this one row.
        setup_session.add(AvatarTemplate(slug="peasant-avatar", name="Peasant Avatar"))
        setup_session.commit()

    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    """One test = one DB transaction, rolled back at teardown.

    join_transaction_mode="create_savepoint" is required because service-layer
    code (veil_service.enter_veil/claim_run) calls session.commit() itself; that
    mode makes such a commit only release a SAVEPOINT, keeping the outer
    transaction alive so the whole test can still be rolled back here.
    """
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """TestClient whose requests run inside this test's db_session transaction,
    so anything an endpoint commits is still rolled back by db_session's teardown.
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def hero_factory(db_session):
    def _make(**overrides) -> Hero:
        user = User(email=f"{uuid.uuid4()}@test.com", hashed_password="x")
        db_session.add(user)
        db_session.flush()
        avatar = db_session.query(AvatarTemplate).filter_by(slug="peasant-avatar").one()
        defaults = dict(
            user_id=user.id,
            avatar_template_id=avatar.id,
            name="Test Hero",
            strength=10,
            dexterity=10,
            vitality=10,
            agility=10,
            intelligence=10,
            spirit=10,
        )
        defaults.update(overrides)
        defaults.setdefault("current_hp", hero_service.compute_max_hp(defaults["vitality"]))
        hero = Hero(**defaults)
        db_session.add(hero)
        db_session.flush()
        return hero

    return _make
