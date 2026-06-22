# Architecture Decisions

Key design choices for the simplified claims processing system. Written to explain trade-offs in a take-home or interview context.

---

## RPC-Style Action Endpoints

### Decision

Claim lifecycle operations are exposed as explicit actions:

```
POST /claims/{id}/adjudicate
POST /claims/{id}/pay
```

rather than generic state updates like `PATCH /claims/{id}` with a `status` field.

### Why

Insurance operations are **domain verbs**, not arbitrary CRUD. "Adjudicate" and "pay" carry specific business meaning — coverage evaluation, deductible math, annual limits — that a generic status patch would hide.

Action endpoints are:

- **Easier to explain** in a 24–48 hour assignment
- **Self-documenting** in Swagger (`/adjudicate` vs inferring valid status values)
- **Safer** — clients cannot skip adjudication and jump directly to `PAID`

### Trade-off

These are RPC-style calls dressed in REST URLs. They are not idempotent and do not use hypermedia. In production, we might add idempotency keys or event-driven processing, but the action-oriented surface matches how adjusters think about the workflow.

---

## Seed Data Instead of Setup APIs

### Decision

Members, policies, and coverage rules are loaded via `python -m app.db.seed`, not `POST /members` or `POST /policies`.

### Why

The assignment goal is **claims processing**, not plan administration. Full CRUD for six entities would:

- Double the API surface without demonstrating adjudication skill
- Introduce authorization questions (who can create policies?)
- Distract from the core loop: submit → adjudicate → explain → dispute

Seed data gives reviewers a **one-command demo** while keeping the API focused on the claim lifecycle.

### Trade-off

The API is not self-contained — clients need pre-existing member IDs. For a take-home, a seed script is an honest scope boundary. Production would expose admin APIs or integrate with an enrollment system.

---

## Intentionally Limited Scope

### What was included

| Layer | Scope |
|-------|--------|
| Domain | 6 entities, line-level adjudication, dispute filing |
| Services | Adjudication engine, claim lifecycle, dispute validation |
| API | Claim submission, adjudication, payment, disputes |
| Tests | Business behavior tests + API integration tests |

### What was excluded

- Authentication and authorization
- Pagination and list endpoints
- Repository abstractions
- Background jobs and async processing
- Provider contracts, fee schedules, prior auth
- Dispute resolution and re-adjudication
- Multi-policy members, benefit period rollover

### Why

A take-home should demonstrate **judgment about what to leave out**. Every excluded item is a conscious deferral, not an oversight. The system is complete enough to run a claim end-to-end and explain every decision.

---

## State Transition Validation in the Service Layer

### Decision

Rules like "only `SUBMITTED` claims can be adjudicated" and "only `APPROVED`/`PARTIALLY_APPROVED` claims can be paid" live in `app/services/`, not in API controllers.

Invalid transitions return **HTTP 409 Conflict**, not 400.

### Why

Controllers should orchestrate HTTP concerns (request parsing, commit, response mapping). Business rules belong in services so they are:

- Testable without HTTP
- Reusable if a CLI or message consumer is added later
- Consistent — one place owns each transition rule

`409` signals that the request was valid but conflicts with current state — the right semantic for "this claim is already paid."

---

## What Would Be Added in Production

| Area | Addition |
|------|----------|
| **Auth** | OAuth2 / API keys; role-based access (member, adjuster, admin) |
| **Enrollment APIs** | Member and policy management, or integration with an external eligibility system |
| **Dispute resolution** | `PATCH /disputes/{id}` to resolve/reject, trigger re-adjudication |
| **Structured errors** | Machine-readable error codes (`CLAIM_NOT_SUBMITTED`, `ANNUAL_LIMIT_REACHED`) |
| **Idempotency** | `Idempotency-Key` header on submit and pay |
| **Audit log** | Immutable event stream for every status change and adjudication decision |
| **Async adjudication** | Queue-based processing for high volume; webhook on completion |
| **PostgreSQL** | Replace SQLite; connection pooling, read replicas |
| **API versioning** | `/v1/claims` prefix |
| **Observability** | Structured logging, metrics, tracing on adjudication pipeline |
| **Input validation** | `date_of_service` eligibility checks, duplicate line detection at submit time |

---

## Summary

This project optimizes for **clarity and explainability** over enterprise completeness. RPC-style endpoints match insurance workflows. Seed data keeps scope tight. Service-layer validation and `409` responses show awareness of production patterns without over-engineering a take-home.
