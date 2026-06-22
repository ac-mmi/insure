# Database Migrations

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Models live in `app/models/` and register with `Base.metadata` via `app/models/__init__.py`.

## Prerequisites

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Ensure `DATABASE_URL` is set in `.env` (default: `sqlite:///./insure.db`).

## Initial Setup

```bash
# Apply all migrations to create tables
alembic upgrade head
```

## Creating a New Migration

After changing SQLAlchemy models:

```bash
# Autogenerate a revision from model diffs
alembic revision --autogenerate -m "describe your change"

# Review the generated file in alembic/versions/ before applying

# Apply the migration
alembic upgrade head
```

## Common Commands

| Command | Description |
|---------|-------------|
| `alembic current` | Show current revision |
| `alembic history` | List all revisions |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one revision |
| `alembic downgrade base` | Drop all migrations (empty schema) |

## Fresh Database

To reset SQLite and reapply from scratch:

```bash
rm -f insure.db
alembic upgrade head
```

## Notes

- `alembic/env.py` imports `app.models` so all tables are visible to autogenerate.
- SQLite uses `render_as_batch=True` for ALTER TABLE support.
- Enum columns use `native_enum=False` (stored as VARCHAR).
- Money fields use `Numeric(10, 2)`; percentages use `Numeric(5, 4)`.
