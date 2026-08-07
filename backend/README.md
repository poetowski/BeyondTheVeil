# Backend

FastAPI + SQLAlchemy + Alembic, PostgreSQL persistence.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # adjust DATABASE_URL if needed
```

Create the database (Postgres user/db matching `DATABASE_URL`), then:

```bash
alembic upgrade head
python -m scripts.seed_dev_data   # optional: dev item/monster content
```

Run the API:

```bash
uvicorn app.main:app --reload
```

## Tests

Tests run against a separate database (`TEST_DATABASE_URL`, defaults to
`.../beyondtheveil_test`):

```bash
pytest
```

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic check   # verify no model/migration drift
```
