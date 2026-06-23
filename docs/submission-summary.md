# Submission Summary

Quick reference for reviewers evaluating this take-home assignment.

---

## Architecture

Three-layer monolith:

```
FastAPI (api/)  →  Services (services/)  →  SQLAlchemy models (models/)  →  SQLite
```

- **Pydantic schemas** decouple API contracts from ORM models
- **Alembic** manages schema migrations
- **Exception handlers** map domain errors to HTTP status codes

Request flow: validate input → call service → commit transaction → return response.

---

## Major Components

| Component | File(s) | Purpose |
|-----------|---------|---------|
| **Adjudication engine** | `app/services/adjudication.py` | Line-level coverage, deductible, limit, and rollup logic |
| **Claim lifecycle** | `app/services/claims.py` | Create, retrieve, pay claims |
| **Dispute workflow** | `app/services/dispute.py` | File disputes with status validation |
| **REST API** | `app/api/claims.py` | Claims and disputes endpoints |
| **ORM models** | `app/models/` | Six entities with enums and constraints |
| **Seed data** | `app/db/seed.py` | Demo policy, member, coverage rules |

---

## Test Coverage Summary

**37 tests, all passing.**

| Suite | Count | Covers |
|-------|-------|--------|
| `tests/services/` | 25 | Adjudication pipeline, rollup, dispute rules |
| `tests/api/` | 11 | HTTP endpoints, status codes, validation |
| `tests/test_health.py` | 1 | Health check |

### Service tests by scenario

| Scenario | File |
|----------|------|
| Covered service approval | `test_covered_service_approval.py` |
| Service not covered | `test_service_not_covered.py` |
| Deductible application | `test_deductible_application.py` |
| Coverage % override | `test_coverage_percentage_override.py` |
| Annual limit exhaustion | `test_annual_limit_exhaustion.py` |
| Claim status rollup | `test_claim_rollup.py` |
| Dispute creation rules | `test_dispute_creation.py` |

Tests were written **before** adjudication implementation (TDD). API tests verify integration with the service layer.

---

## API Summary

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness and DB connectivity |
| `POST` | `/claims` | Submit claim with line items |
| `GET` | `/claims/{id}` | Get claim with line items and explanations |
| `POST` | `/claims/{id}/adjudicate` | Run adjudication engine |
| `POST` | `/claims/{id}/pay` | Mark claim as paid |
| `POST` | `/claims/{id}/disputes` | File a dispute |
| `GET` | `/claims/{id}/disputes` | List disputes |

### HTTP status codes

| Code | Usage |
|------|-------|
| `201` | Claim or dispute created |
| `200` | Successful read or action |
| `400` | Business rule failure (adjudication error) |
| `404` | Claim or member not found |
| `409` | Invalid state transition |
| `422` | Request validation failure |

No authentication. No pagination. No list-all endpoints.

Detail: [api.md](api.md)

---

## Business Rules Implemented

| Rule | Implementation |
|------|----------------|
| Coverage rule lookup by `(policy_id, service_code)` | `adjudicate_line_item()` |
| Deny if no rule or `is_covered=false` | Returns explanation: "Service not covered under policy" |
| Deductible applied before insurer payment | Member `deductible_met` updated; no coverage % until met |
| Coverage % from override or policy default | `coverage_percentage_override ?? policy.coverage_percentage` |
| Annual limit caps insurer payment | `amount_paid_ytd` updated; deny if limit exhausted |
| Line-level approve/deny with explanation | `ClaimLineItem.status` + `explanation` |
| Claim status rollup from line outcomes | `rollup_claim_status()` |
| Disputes on DENIED or PARTIALLY_APPROVED only | `create_dispute()` + `StateConflictError` |
| State guards in service layer | `SUBMITTED` for adjudicate; `APPROVED`/`PARTIALLY_APPROVED` for pay |

---

## Scope Decisions

### Included (demonstrates core skills)

- Domain research and modeling
- SQLAlchemy 2.x typed ORM with migrations
- TDD for adjudication behavior
- Service layer with clear business rules
- REST API with proper HTTP semantics
- Human-readable explanations on every decision
- Seed data for one-command demo

### Excluded (intentional)

| Excluded | Reason |
|----------|--------|
| Authentication / authorization | Out of scope; adds complexity without demonstrating domain skill |
| Member/Policy CRUD APIs | Seed script sufficient; keeps API focused on claims |
| Provider entity | Enterprise modeling distraction |
| Fee schedules / prior auth | Enterprise insurance complexity |
| Dispute resolution | Filing disputes demonstrates the model; resolution is a natural extension |
| Pagination / list endpoints | Not needed for demo; adds API surface |
| Repository pattern | Service layer is thin enough |
| Background jobs / async | Synchronous adjudication is fine at this scale |
| PostgreSQL | SQLite is zero-config for reviewers |

### Why this scope

A 24–48 hour take-home should show **judgment about what to build and what to defer**. This project prioritizes:

1. **Correct adjudication logic** with tests
2. **Explainable outcomes** visible in the API
3. **Clean layering** that is easy to walk through in an interview
4. **Honest documentation** of tradeoffs

It does not attempt to be a production insurance platform.

---

## How to Evaluate

```bash
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
pytest
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000/docs
```

Suggested review order:

1. [domain-model.md](domain-model.md) — understand the model
2. `tests/services/` — see expected behavior
3. `app/services/adjudication.py` — see implementation
4. [api.md](api.md) — run the walkthrough
5. [self-review.md](self-review.md) — known limitations

---

## Documentation Index

| File | Purpose |
|------|---------|
| [README.md](../README.md) | Project entry point |
| [domain-model.md](domain-model.md) | Entity spec and state machines |
| [claims-processing-research.md](claims-processing-research.md) | Domain research |
| [architecture-decisions.md](architecture-decisions.md) | Design rationale |
| [project-structure.md](project-structure.md) | Code layout |
| [api.md](api.md) | API reference |
| [migrations.md](migrations.md) | Database migrations |
| [self-review.md](self-review.md) | Honest self-assessment |
