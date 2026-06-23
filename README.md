# Insure — Simplified Health Insurance Claims Processing

A take-home assignment implementing a minimal claims processing system: submit claims, adjudicate line items, explain decisions, and file disputes.

Built with **FastAPI**, **SQLAlchemy 2.x**, **SQLite**, **Alembic**, **Pydantic v2**, and **Pytest**.

---

## Problem Statement

Health insurance claims processing involves evaluating whether services are covered, applying cost-sharing rules (deductibles, coverage percentages, annual limits), and producing explainable outcomes at the line-item level. Real systems are complex; this project implements a **deliberately simplified** version that demonstrates domain modeling and engineering judgment within a 24–48 hour scope.

**Core workflow:**

```
Submit claim → Adjudicate lines → Review explanations → Pay (if approved) → Dispute (if denied)
```

---

## Architecture Overview

```
HTTP Request
    │
    ▼
app/api/          Route handlers, Pydantic validation, HTTP status codes
    │
    ▼
app/services/     Adjudication, claim lifecycle, dispute validation
    │
    ▼
app/models/       SQLAlchemy ORM
    │
    ▼
SQLite
```

| Layer | Responsibility |
|-------|----------------|
| `api/` | HTTP concerns only — delegates to services |
| `services/` | Business rules, state transitions, adjudication math |
| `models/` | Persistence — six domain entities |
| `schemas/` | API request/response contracts (Pydantic v2) |
| `db/` | Engine, sessions, migrations, seed data |

See [docs/project-structure.md](docs/project-structure.md) and [docs/architecture-decisions.md](docs/architecture-decisions.md) for detail.

---

## Domain Model Summary

Six entities — no more:

| Entity | Role |
|--------|------|
| **Policy** | Plan config: deductible, coverage %, annual limit |
| **Member** | Insured person; tracks `deductible_met` and `amount_paid_ytd` |
| **CoverageRule** | Per-service coverage gate; optional coverage % override |
| **Claim** | Reimbursement request; status is a rollup of line outcomes |
| **ClaimLineItem** | Atomic unit of adjudication; carries `explanation` |
| **Dispute** | Appeal filed against denied or partially approved claims |

**Relationships:** Policy → many Members. Member → many Claims. Claim → many ClaimLineItems and Disputes.

Full spec: [docs/domain-model.md](docs/domain-model.md)

---

## Key Business Rules

1. **Coverage gate** — No matching rule or `is_covered=false` → line denied with explanation.
2. **Deductible** — Applied before insurer payment when `deductible_met < policy.deductible`. Coverage % does not apply until deductible is met.
3. **Coverage percentage** — Uses `coverage_percentage_override` on the matched rule, else `policy.coverage_percentage`.
4. **Annual limit** — Insurer payment capped at `annual_limit - amount_paid_ytd`. Zero remaining → denied.
5. **Line-level decisions** — Each line adjudicated independently; claim status is derived.
6. **Claim rollup** — All approved → `APPROVED`; all denied → `DENIED`; mixed → `PARTIALLY_APPROVED`.
7. **Explainability** — Every approved or denied line has a human-readable `explanation`.
8. **Disputes** — Allowed only on `DENIED` or `PARTIALLY_APPROVED` claims.

---

## Setup

**Requirements:** Python 3.9+

```bash
# Clone and enter project
cd insure

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Environment (optional — defaults work)
cp .env.example .env

# Database migrations
alembic upgrade head

# Seed demo data
python -m app.db.seed
```

---

## Running the Server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

---

## Running Tests

```bash
source .venv/bin/activate
pytest
```

**37 tests** — service behavior, API integration, health check.

```bash
pytest tests/services/ -v   # adjudication and dispute logic
pytest tests/api/ -v        # HTTP endpoints
```

---

## Seed Data

```bash
python -m app.db.seed
```

Creates:

| Item | Values |
|------|--------|
| Policy | Gold PPO 2026 — $1,000 deductible, 80% coverage, $10,000 annual limit |
| Member | Jane Doe — deductible already met ($1,000) |
| Coverage rules | `99213` office visit (covered), `92004` vision (90% override), `D2750` dental crown (not covered) |

Output includes `member_id` for API requests. Re-running is idempotent.

---

## API Walkthrough

```bash
# 1. Seed data and note member_id
python -m app.db.seed

# 2. Submit a claim with two line items
curl -s -X POST http://127.0.0.1:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "<MEMBER_ID>",
    "provider_name": "City Medical Center",
    "date_of_service": "2026-03-15",
    "line_items": [
      {"service_code": "99213", "description": "Office visit", "billed_amount": "500.00"},
      {"service_code": "D2750", "description": "Dental crown", "billed_amount": "1200.00"}
    ]
  }'

# 3. Adjudicate (save claim_id from step 2)
curl -s -X POST http://127.0.0.1:8000/claims/<CLAIM_ID>/adjudicate | python -m json.tool

# 4. File a dispute on the denied dental line
curl -s -X POST http://127.0.0.1:8000/claims/<CLAIM_ID>/disputes \
  -H "Content-Type: application/json" \
  -d '{"reason": "Dental should be covered."}'

# 5. Pay the approved portion
curl -s -X POST http://127.0.0.1:8000/claims/<CLAIM_ID>/pay | python -m json.tool
```

**Expected adjudication outcome:** Office visit approved at $400 (80% of $500). Dental crown denied — not covered. Claim status: `PARTIALLY_APPROVED`.

Full reference: [docs/api.md](docs/api.md)

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Six entities only | Avoid enterprise complexity (providers, fee schedules, accumulators as separate tables) |
| Line items as adjudication unit | Enables partial approvals and per-line explanations |
| RPC-style `/adjudicate` and `/pay` | Maps to insurance verbs; clearer than generic status PATCH |
| Seed script instead of admin APIs | Keeps API focused on claims workflow |
| Service-layer state validation | Testable without HTTP; returns `409 Conflict` for invalid transitions |
| Tests before adjudication implementation | TDD — behavior defined before code |
| SQLite | Zero external dependencies for reviewers |

Detail: [docs/architecture-decisions.md](docs/architecture-decisions.md)

---

## Tradeoffs

**Chose clarity over completeness.**

- No authentication, pagination, or async processing
- Provider is a string, not an entity
- No dispute resolution or re-adjudication endpoints
- `UNDER_REVIEW` exists in the domain but is not exposed to API clients
- Member/policy setup requires seed script, not API
- Flat error responses (`{detail: string}`) without machine-readable codes
- Naive UTC timestamps

These are intentional scope boundaries for a take-home, not oversights.

---

## Future Improvements

See [docs/architecture-decisions.md](docs/architecture-decisions.md#what-would-be-added-in-production). Highlights:

- Auth and role-based access
- Enrollment/admin APIs
- Dispute resolution workflow
- Structured error codes
- PostgreSQL, idempotency keys, audit event log
- Submit-time validation (eligibility, duplicate line detection)

---

## Documentation Index

| Document | Contents |
|----------|----------|
| [docs/domain-model.md](docs/domain-model.md) | Entities, state machines, adjudication pipeline |
| [docs/claims-processing-research.md](docs/claims-processing-research.md) | Domain research notes |
| [docs/project-structure.md](docs/project-structure.md) | Folder layout and request flow |
| [docs/architecture-decisions.md](docs/architecture-decisions.md) | Why RPC endpoints, seed data, 409 responses |
| [docs/api.md](docs/api.md) | Endpoint reference and examples |
| [docs/migrations.md](docs/migrations.md) | Alembic commands |
| [docs/submission-summary.md](docs/submission-summary.md) | Reviewer quick reference |
| [docs/self-review.md](docs/self-review.md) | Honest strengths and weaknesses |

---

## Tech Stack

- FastAPI
- SQLAlchemy 2.x (typed ORM)
- SQLite
- Alembic
- Pydantic v2
- Pytest
