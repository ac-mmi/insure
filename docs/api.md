# API Reference

REST API for the simplified health insurance claims processing system.

**Base URL:** `http://127.0.0.1:8000`

**Interactive docs:** [Swagger UI](http://127.0.0.1:8000/docs) · [ReDoc](http://127.0.0.1:8000/redoc)

---

## Quick Start

```bash
source .venv/bin/activate
uvicorn app.main:app --reload

# Load demo policy, member, and coverage rules
python -m app.db.seed
```

Save the printed `member_id` for claim requests.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/claims` | Submit a claim with line items |
| `GET` | `/claims/{claim_id}` | Retrieve claim and line items |
| `POST` | `/claims/{claim_id}/adjudicate` | Run adjudication |
| `POST` | `/claims/{claim_id}/pay` | Mark claim as paid |
| `POST` | `/claims/{claim_id}/disputes` | File a dispute |
| `GET` | `/claims/{claim_id}/disputes` | List disputes for a claim |

---

## Error Responses

All errors return:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | When |
|--------|------|
| `400` | Invalid operation (wrong claim status, dispute rejected) |
| `404` | Claim or member not found |
| `422` | Request validation failed |

---

## Claims

### POST /claims

Submit a new claim with one or more line items.

**Request**

```json
{
  "member_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "provider_name": "City Medical Center",
  "date_of_service": "2026-03-15",
  "line_items": [
    {
      "service_code": "99213",
      "description": "Office visit — established patient",
      "billed_amount": "500.00"
    },
    {
      "service_code": "D2750",
      "description": "Dental crown",
      "billed_amount": "1200.00"
    }
  ]
}
```

**Response `201`**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "member_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "provider_name": "City Medical Center",
  "date_of_service": "2026-03-15",
  "status": "SUBMITTED",
  "submitted_at": "2026-03-15T10:30:00",
  "adjudicated_at": null,
  "paid_at": null,
  "created_at": "2026-03-15T10:30:00",
  "line_items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "claim_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "service_code": "99213",
      "description": "Office visit — established patient",
      "billed_amount": "500.00",
      "approved_amount": null,
      "status": "PENDING",
      "explanation": null,
      "created_at": "2026-03-15T10:30:00"
    }
  ]
}
```

**curl**

```bash
curl -X POST http://127.0.0.1:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "<MEMBER_ID>",
    "provider_name": "City Medical Center",
    "date_of_service": "2026-03-15",
    "line_items": [
      {
        "service_code": "99213",
        "description": "Office visit",
        "billed_amount": "500.00"
      }
    ]
  }'
```

---

### GET /claims/{claim_id}

Retrieve a claim with all line items and adjudication explanations.

**Response `200`** — same shape as create response, with updated statuses after adjudication.

**curl**

```bash
curl http://127.0.0.1:8000/claims/<CLAIM_ID>
```

---

### POST /claims/{claim_id}/adjudicate

Run the adjudication engine on all line items. Claim must be in `SUBMITTED` status.

**Response `200`**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "PARTIALLY_APPROVED",
  "adjudicated_at": "2026-03-15T10:35:00",
  "line_items": [
    {
      "service_code": "99213",
      "status": "APPROVED",
      "billed_amount": "500.00",
      "approved_amount": "400.00",
      "explanation": "Covered service. 80% coverage applied."
    },
    {
      "service_code": "D2750",
      "status": "DENIED",
      "billed_amount": "1200.00",
      "approved_amount": "0.00",
      "explanation": "Service not covered under policy"
    }
  ]
}
```

**curl**

```bash
curl -X POST http://127.0.0.1:8000/claims/<CLAIM_ID>/adjudicate
```

---

### POST /claims/{claim_id}/pay

Mark an `APPROVED` or `PARTIALLY_APPROVED` claim as `PAID`.

**Response `200`**

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "PAID",
  "paid_at": "2026-03-15T11:00:00"
}
```

**Response `400`** — claim not in a payable status.

**curl**

```bash
curl -X POST http://127.0.0.1:8000/claims/<CLAIM_ID>/pay
```

---

## Disputes

### POST /claims/{claim_id}/disputes

File a dispute against a `DENIED` or `PARTIALLY_APPROVED` claim.

**Request**

```json
{
  "reason": "The denied dental service should be covered under my plan."
}
```

**Response `201`**

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "claim_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "reason": "The denied dental service should be covered under my plan.",
  "status": "OPEN",
  "resolution_notes": null,
  "created_at": "2026-03-15T12:00:00",
  "resolved_at": null
}
```

**Response `400`** — claim is `APPROVED`, `SUBMITTED`, or otherwise not disputable.

**curl**

```bash
curl -X POST http://127.0.0.1:8000/claims/<CLAIM_ID>/disputes \
  -H "Content-Type: application/json" \
  -d '{"reason": "Please review the denied line item."}'
```

---

### GET /claims/{claim_id}/disputes

List all disputes filed against a claim.

**Response `200`**

```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "claim_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "reason": "Please review the denied line item.",
    "status": "OPEN",
    "resolution_notes": null,
    "created_at": "2026-03-15T12:00:00",
    "resolved_at": null
  }
]
```

**curl**

```bash
curl http://127.0.0.1:8000/claims/<CLAIM_ID>/disputes
```

---

## End-to-End Example

```bash
# 1. Start server and seed data
uvicorn app.main:app --reload
python -m app.db.seed
# Note member_id from output

# 2. Submit a mixed claim (one covered, one not)
CLAIM=$(curl -s -X POST http://127.0.0.1:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "<MEMBER_ID>",
    "provider_name": "City Medical Center",
    "date_of_service": "2026-03-15",
    "line_items": [
      {"service_code": "99213", "description": "Office visit", "billed_amount": "500.00"},
      {"service_code": "D2750", "description": "Dental crown", "billed_amount": "1200.00"}
    ]
  }')

CLAIM_ID=$(echo $CLAIM | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 3. Adjudicate
curl -X POST http://127.0.0.1:8000/claims/$CLAIM_ID/adjudicate | python -m json.tool

# 4. File dispute on partial denial
curl -X POST http://127.0.0.1:8000/claims/$CLAIM_ID/disputes \
  -H "Content-Type: application/json" \
  -d '{"reason": "Dental should be covered."}'

# 5. Pay approved portion
curl -X POST http://127.0.0.1:8000/claims/$CLAIM_ID/pay | python -m json.tool
```

---

## Schemas

Response schemas are available in OpenAPI at `/openapi.json`. Key models:

| Schema | Purpose |
|--------|---------|
| `ClaimCreate` / `ClaimRead` | Claim submission and retrieval |
| `ClaimLineItemCreate` / `ClaimLineItemRead` | Line item input and adjudication output |
| `DisputeCreate` / `DisputeRead` | Dispute filing and listing |
| `MemberRead` | Member with policy (for future use) |
| `PolicyRead` | Plan configuration |
| `CoverageRuleRead` | Service coverage rules |

Line item `explanation` fields contain human-readable adjudication decisions after `/adjudicate` is called.
