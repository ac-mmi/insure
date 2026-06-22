# Project Structure

Infrastructure layout for the simplified health insurance claims processing system. This document describes folder responsibilities and how future implementation phases map onto the structure.

---

## Directory Tree

```
insure/
├── alembic/                  # Database migrations
│   ├── versions/             # Migration revision files
│   ├── env.py                # Alembic runtime configuration
│   └── script.py.mako        # Migration file template
├── app/                      # Application package
│   ├── api/                  # HTTP route handlers
│   │   ├── health.py         # Health check endpoint
│   │   └── router.py         # Aggregates all API routers
│   ├── core/                 # Cross-cutting application config
│   │   └── config.py         # Settings via environment variables
│   ├── db/                   # Database engine and session setup
│   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   └── database.py       # Engine, session factory, get_db
│   ├── models/               # SQLAlchemy ORM models (future)
│   ├── schemas/              # Pydantic request/response models
│   │   └── health.py         # Health check response schema
│   ├── services/             # Business logic layer (future)
│   └── main.py               # FastAPI app factory and entrypoint
├── docs/                     # Design and project documentation
├── tests/                    # Pytest test suite
│   ├── conftest.py           # Shared fixtures (client, db session)
│   └── test_health.py        # Health endpoint tests
├── alembic.ini               # Alembic CLI configuration
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variable template
```

---

## Folder Responsibilities

### `app/`

The root application package. All runtime code lives here. `main.py` is the single entrypoint that wires configuration, database lifecycle, and API routers into a FastAPI application.

### `app/api/`

**HTTP layer only.** Route handlers validate input via Pydantic schemas, call services, and return responses. No business logic or direct SQLAlchemy queries beyond trivial health checks.

| File | Purpose |
|------|---------|
| `router.py` | Central router that includes all feature routers |
| `health.py` | `GET /health` — liveness and database connectivity |

**Future phase:** Add `claims.py`, `disputes.py`, `members.py`, etc. Each file owns one resource's endpoints.

### `app/core/`

**Application-wide configuration and utilities.** Settings that don't belong to any single feature.

| File | Purpose |
|------|---------|
| `config.py` | `pydantic-settings` model loaded from environment / `.env` |

Keeps configuration out of route handlers and services. Values like `DATABASE_URL` and `DEBUG` are read once and cached.

### `app/db/`

**Database infrastructure.** Engine creation, session management, and the declarative base for ORM models.

| File | Purpose |
|------|---------|
| `base.py` | `DeclarativeBase` subclass — all models inherit from this |
| `database.py` | Engine, `SessionLocal`, `get_db()` dependency, `init_db()` |

`get_db()` is injected into FastAPI routes via `Depends()`. Sessions are opened per request and closed in a `finally` block.

### `app/models/`

**SQLAlchemy ORM models.** One file per entity, mapping database tables to Python classes.

Currently empty. **Future phase:** Add `member.py`, `policy.py`, `coverage_rule.py`, `claim.py`, `claim_line_item.py`, `dispute.py` per `docs/domain-model.md`.

Models are imported in `app/models/__init__.py` so Alembic discovers them via `Base.metadata`.

### `app/schemas/`

**Pydantic v2 models for API contracts.** Separate from ORM models — schemas define what the API accepts and returns.

| File | Purpose |
|------|---------|
| `health.py` | `HealthResponse` for the health endpoint |

**Future phase:** Add `claim.py`, `claim_line_item.py`, etc. with `Create`, `Read`, and `Update` variants. Schemas decouple the HTTP contract from the database shape.

### `app/services/`

**Business logic layer.** Pure domain operations with no HTTP or framework dependencies.

Currently empty. **Future phase:** Add `adjudication.py` (line-level adjudication + claim rollup), `dispute.py` (open / resolve / reject). Services receive a `Session` and domain objects, return results. API routes call services; services call models.

This separation keeps adjudication logic testable without HTTP.

### `alembic/`

**Database schema migrations.** Version-controlled DDL changes applied via `alembic upgrade head`.

`env.py` reads `DATABASE_URL` from application settings and uses `Base.metadata` as the migration target. `render_as_batch=True` supports SQLite's limited `ALTER TABLE` support.

**Future phase:** After models are created, run `alembic revision --autogenerate -m "initial schema"` to generate the first migration.

### `tests/`

**Automated test suite.** Mirrors `app/` structure as features are added.

| File | Purpose |
|------|---------|
| `conftest.py` | In-memory SQLite engine, session override, `TestClient` fixture |
| `test_health.py` | Verifies health endpoint returns 200 with expected fields |

**Future phase:** Add `tests/services/test_adjudication.py`, `tests/api/test_claims.py`, etc.

### `docs/`

**Design documentation.** Not executed at runtime.

| File | Purpose |
|------|---------|
| `domain-model.md` | Entity definitions, state machines, adjudication logic |
| `claims-processing-research.md` | Domain research notes |
| `project-structure.md` | This file |

---

## Request Flow (Target Architecture)

```
HTTP Request
    │
    ▼
app/api/          ← route handler, input validation (Pydantic)
    │
    ▼
app/services/     ← business logic (adjudication, disputes)
    │
    ▼
app/models/       ← SQLAlchemy ORM, database reads/writes
    │
    ▼
SQLite
```

Configuration flows from `app/core/config.py` into `app/db/database.py` and is available everywhere via `settings`.

---

## Future Implementation Phases

| Phase | What gets added | Where |
|-------|-----------------|-------|
| **1 — Infrastructure** (current) | Config, DB, health check, Alembic, pytest | `core/`, `db/`, `api/health.py`, `tests/` |
| **2 — Data models** | Member, Policy, CoverageRule, Claim, ClaimLineItem, Dispute | `app/models/`, Alembic migration |
| **3 — API schemas** | Create/Read/Update Pydantic models per entity | `app/schemas/` |
| **4 — Adjudication service** | Line-level adjudication pipeline, claim status rollup | `app/services/adjudication.py` |
| **5 — Claim endpoints** | Submit, adjudicate, list, get claim | `app/api/claims.py` |
| **6 — Dispute endpoints** | File, resolve, reject disputes | `app/api/disputes.py`, `app/services/dispute.py` |
| **7 — Seed data** | Sample policies, members, coverage rules for demo | `app/db/seed.py` or Alembic data migration |
| **8 — Integration tests** | End-to-end claim submission and adjudication | `tests/` |

Each phase adds files to existing folders rather than restructuring. The layout is stable from infrastructure through full feature delivery.

---

## Design Rationale

**Why separate `models/` and `schemas/`?**  
ORM models reflect database columns and relationships. API schemas reflect what clients send and receive. They diverge — e.g., a `ClaimRead` schema includes nested line items; a `Claim` model does not expose internal fields.

**Why a `services/` layer?**  
Adjudication involves deductible math, coverage rule matching, and status rollup. Putting that in route handlers makes it untestable and mixes HTTP concerns with domain logic.

**Why SQLite?**  
Zero external dependencies for a take-home. SQLAlchemy abstracts the dialect; switching to PostgreSQL later is a config change.

**Why Alembic from day one?**  
Even with `create_all()` for development, migrations provide a reproducible schema history reviewers can inspect. Autogenerate works once models exist.

**Why `create_app()` factory?**  
Tests create a fresh app instance with dependency overrides. Production uses the module-level `app` in `main.py` for uvicorn.
