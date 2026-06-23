# Self-Review

An honest assessment of what worked, what was simplified, and what I would change with more time.

---

## Strengths

### What went well

- **Domain-first approach** — Research and modeling happened before code. The six-entity model stayed stable through implementation.
- **Test-driven adjudication** — Business behavior tests were written before the adjudication engine. That forced clear thinking about deductible math, overrides, and rollup rules.
- **Readable service layer** — `adjudication.py` follows the documented pipeline step-by-step. No abstractions that exist "for future use."
- **Explainable outcomes** — Every line item gets a human-readable `explanation`. This was a requirement from day one and is visible in API responses.
- **Layered architecture** — API → services → models is consistent. State transition rules live in services, not controllers.
- **End-to-end demo path** — Seed script + curl walkthrough lets a reviewer run the full workflow in minutes.

### Engineering decisions I am happy with

| Decision | Why |
|----------|-----|
| Line-level adjudication with claim rollup | Matches real EOB behavior; enables partial approvals |
| `coverage_percentage_override` on CoverageRule | Handles vision/dental rates without duplicating policies |
| Accumulators on Member, config on Policy | Clean separation of template vs runtime state |
| `StateConflictError` → HTTP 409 | Correct semantic for invalid state transitions |
| Pydantic validators + service validation for disputes | Defense in depth without over-engineering |
| Alembic from the start | Reviewers can inspect schema history |
| RPC-style action endpoints | Honest about insurance being verb-oriented |

---

## Weaknesses

### Simplifications made

- **Deductible logic is linear** — When deductible is unmet, coverage percentage is not applied to the post-deductible remainder. This matches the tests but is simpler than some real plans.
- **No fee schedules** — Allowed amount equals billed amount (before cost-sharing). Real systems negotiate contracted rates.
- **Static accumulators** — `deductible_met` and `amount_paid_ytd` never reset. No benefit period concept.
- **Provider as a string** — No network tier, NPI, or contract pricing.
- **Dispute filing only** — No resolve/reject workflow or re-adjudication trigger.
- **Single policy per member** — No coordination of benefits or plan changes mid-year.

### Known limitations

| Limitation | Impact |
|------------|--------|
| No auth | Anyone with the API can submit claims or adjudicate |
| No list endpoints | Cannot browse claims — get-by-id only |
| Seed required for setup | API is not self-contained for first use |
| `GET /claims/{id}` omits disputes | Requires separate call to list disputes |
| Flat error format | Clients parse message strings, not error codes |
| `create_all()` on startup + Alembic | Redundant paths; fine for SQLite demo |
| Duplicate claim-loading queries | `_load_claim` in services vs `_load_claim_with_disputes` in API |
| No submit-time validation | Bad service codes only fail at adjudication |
| `$0` approved lines | Covered lines with full deductible absorption show `APPROVED` with `approved_amount: 0` — correct per rules but potentially confusing |

---

## If Given Another Week

### What I would improve

1. **Consolidate claim loading** — Single service method with optional `include_disputes`. Remove SQLAlchemy from the API layer entirely.
2. **Structured error responses** — Add `code` field (`CLAIM_NOT_SUBMITTED`, `ANNUAL_LIMIT_REACHED`) alongside `detail`.
3. **Submit-time validation** — Check coverage rules exist for each line item; return warnings or reject early.
4. **Embed disputes on claim read** — Optional `?include=disputes` or always include in `ClaimRead`.
5. **Dispute resolution API** — `PATCH /disputes/{id}` with re-adjudication on `RESOLVED`.
6. **Idempotent pay** — Return current state on repeat `POST /pay` instead of 409.

### What I would add

1. **Minimal admin endpoints** — `POST /policies`, `POST /members` so the API is self-contained without seed.
2. **Integration test for full walkthrough** — Single test: seed → submit → adjudicate → dispute → pay.
3. **PostgreSQL support** — Docker Compose for local dev; verify Alembic migrations.
4. **Audit event log** — Append-only table for status changes and adjudication decisions.
5. **OpenAPI examples** — Pre-filled request bodies in Swagger for faster reviewer onboarding.

### What I would not add (yet)

- Repository pattern — the service layer is thin enough that it would add indirection without benefit
- Event sourcing — overkill for this scope
- Microservices — a monolith is the right shape here

---

## Summary

The project succeeds at its stated goal: a **clear, explainable, testable** claims processing system that a reviewer can understand and run quickly. It does not pretend to be production-ready insurance software — and the documentation says so explicitly.

The highest-value next step would be dispute resolution and re-adjudication, completing the appeal loop described in the domain model but intentionally deferred in implementation.
