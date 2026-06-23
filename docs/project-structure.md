# Project Structure

Layout for the simplified health insurance claims processing system. Describes folder responsibilities and how components fit together.

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
│   │   ├── claims.py         # Claims and disputes endpoints
│   │   ├── errors.py         # Exception handlers
│   │   ├── health.py         # Health check endpoint
│   │   └── router.py         # Aggregates all API routers
│   ├── core/                 # Cross-cutting application config
│   │   └── config.py         # Settings via environment variables
│   ├── db/                   # Database engine and session setup
│   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   ├── database.py       # Engine, session factory, get_db
│   │   └── seed.py           # Demo data loader
│   ├── models/               # SQLAlchemy ORM models (6 entities)
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # Business logic layer
│   └── main.py               # FastAPI app factory and entrypoint
├── docs/                     # Design and project documentation
├── tests/                    # Pytest test suite
│   ├── api/                  # API integration tests
│   ├── fixtures/             # Test data factories
│   ├── services/             # Business behavior tests
│   └── conftest.py           # Shared fixtures
├── alembic.ini               # Alembic CLI configuration
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variable template
```

---

## Folder Responsibilities

### `app/`

The root application package. `main.py` wires configuration, database lifecycle, exception handlers, and API routers into a FastAPI application.

### `app/api/`

**HTTP layer only.** Route handlers validate input via Pydantic schemas, call services, commit transactions, and return responses.

| File | Purpose |
|------|---------|
| `router.py` | Central router that includes all feature routers |
| `health.py` | `GET /health` — liveness and database connectivity |
| `claims.py` | Claim submission, adjudication, payment, disputes |
| `errors.py` | Maps domain exceptions to HTTP status codes |

State transition rules live in services, not controllers. Invalid transitions return `409 Conflict`.

### `app/core/`

**Application-wide configuration.** Settings loaded from environment / `.env` via `pydantic-settings`.

### `app/db/`

**Database infrastructure.** Engine, session management, declarative base, and seed script.

| File | Purpose |
|------|---------|
| `base.py` | `DeclarativeBase` subclass |
| `database.py` | Engine, `SessionLocal`, `get_db()`, `init_db()` |
| `seed.py` | Demo policy, member, and coverage rules |

### `app/models/`

**SQLAlchemy ORM models.** One file per entity: Member, Policy, CoverageRule, Claim, ClaimLineItem, Dispute.

Models are imported in `app/models/__init__.py` so Alembic discovers them via `Base.metadata`.

### `app/schemas/`

**Pydantic v2 API contracts.** Separate from ORM models.

| File | Purpose |
|------|---------|
| `claim.py` | `ClaimCreate`, `ClaimRead` |
| `claim_line_item.py` | `ClaimLineItemCreate`, `ClaimLineItemRead` |
| `dispute.py` | `DisputeCreate`, `DisputeRead` |
| `member.py`, `policy.py`, `coverage_rule.py` | Read schemas (defined, not yet exposed via API) |

### `app/services/`

**Business logic layer.** No HTTP dependencies.

| File | Purpose |
|------|---------|
| `adjudication.py` | Line-level adjudication, claim rollup |
| `claims.py` | Create, retrieve, pay claims |
| `dispute.py` | File disputes with validation |
| `exceptions.py` | `NotFoundError`, `StateConflictError`, etc. |

### `tests/`

**Automated test suite** — 37 tests.

| Directory | Purpose |
|-----------|---------|
| `services/` | Business behavior tests (TDD for adjudication) |
| `api/` | HTTP endpoint integration tests |
| `fixtures/` | Domain object factories |

### `docs/`

| File | Purpose |
|------|---------|
| `domain-model.md` | Entity definitions, state machines, adjudication logic |
| `claims-processing-research.md` | Domain research notes |
| `architecture-decisions.md` | Design rationale and tradeoffs |
| `api.md` | Endpoint reference and examples |
| `migrations.md` | Alembic commands |
| `submission-summary.md` | Reviewer quick reference |
| `self-review.md` | Honest strengths and weaknesses |
| `project-structure.md` | This file |

---

## Request Flow

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

## Implementation Phases (Completed)

| Phase | Status | Where |
|-------|--------|-------|
| Infrastructure | Done | `core/`, `db/`, `api/health.py`, Alembic, pytest |
| Data models | Done | `app/models/`, initial Alembic migration |
| API schemas | Done | `app/schemas/` |
| Adjudication service | Done | `app/services/adjudication.py` |
| Claim/dispute endpoints | Done | `app/api/claims.py` |
| Seed data | Done | `app/db/seed.py` |
| Tests | Done | `tests/services/`, `tests/api/` |

---

## Design Rationale

**Why separate `models/` and `schemas/`?**  
ORM models reflect database columns and relationships. API schemas reflect what clients send and receive.

**Why a `services/` layer?**  
Adjudication involves deductible math, coverage rule matching, and status rollup. Keeping this out of route handlers makes it testable without HTTP.

**Why SQLite?**  
Zero external dependencies for a take-home. SQLAlchemy abstracts the dialect; switching to PostgreSQL is a config change.

**Why Alembic from day one?**  
Migrations provide a reproducible schema history reviewers can inspect.

**Why `create_app()` factory?**  
Tests create a fresh app instance with dependency overrides.

---

## Possible Extensions (Not Implemented)

- Admin APIs for members and policies
- Dispute resolution endpoints
- Repository pattern (not needed at current scale)
- List/pagination endpoints
- Authentication and authorization

See [architecture-decisions.md](architecture-decisions.md) for production roadmap.
