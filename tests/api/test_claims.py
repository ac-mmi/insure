import uuid

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.enums import ClaimStatus
from tests.fixtures.domain import (
    create_claim,
    create_coverage_rule,
    create_line_item,
    create_member,
    create_policy,
)


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    from app.db.database import get_db
    from app.main import create_app

    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture
def seeded_member(db_session: Session):
    policy = create_policy(db_session)
    create_coverage_rule(
        db_session,
        policy=policy,
        service_code="99213",
        description="Office visit",
        is_covered=True,
    )
    create_coverage_rule(
        db_session,
        policy=policy,
        service_code="D2750",
        description="Dental crown",
        is_covered=False,
    )
    member = create_member(
        db_session,
        policy=policy,
        deductible_met=Decimal("1000.00"),
    )
    db_session.commit()
    return member


class TestClaimsAPI:
    def test_create_claim(self, api_client: TestClient, seeded_member):
        response = api_client.post(
            "/claims",
            json={
                "member_id": str(seeded_member.id),
                "provider_name": "City Medical Center",
                "date_of_service": "2026-03-15",
                "line_items": [
                    {
                        "service_code": "99213",
                        "description": "Office visit",
                        "billed_amount": "500.00",
                    }
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "SUBMITTED"
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["status"] == "PENDING"

    def test_get_claim(self, api_client: TestClient, seeded_member, db_session):
        claim = create_claim(db_session, member=seeded_member)
        create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("500.00"),
        )
        db_session.commit()

        response = api_client.get(f"/claims/{claim.id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(claim.id)

    def test_get_claim_not_found(self, api_client: TestClient):
        response = api_client.get(f"/claims/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_adjudicate_claim(self, api_client: TestClient, seeded_member):
        create_response = api_client.post(
            "/claims",
            json={
                "member_id": str(seeded_member.id),
                "provider_name": "City Medical Center",
                "date_of_service": "2026-03-15",
                "line_items": [
                    {
                        "service_code": "99213",
                        "description": "Office visit",
                        "billed_amount": "500.00",
                    }
                ],
            },
        )
        claim_id = create_response.json()["id"]

        response = api_client.post(f"/claims/{claim_id}/adjudicate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["line_items"][0]["status"] == "APPROVED"
        assert data["line_items"][0]["explanation"] is not None
        assert data["adjudicated_at"] is not None

    def test_pay_claim(self, api_client: TestClient, seeded_member, db_session):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.APPROVED)
        db_session.commit()

        response = api_client.post(f"/claims/{claim.id}/pay")
        assert response.status_code == 200
        assert response.json()["status"] == "PAID"
        assert response.json()["paid_at"] is not None

    def test_pay_claim_invalid_status(self, api_client: TestClient, seeded_member, db_session):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.SUBMITTED)
        db_session.commit()

        response = api_client.post(f"/claims/{claim.id}/pay")
        assert response.status_code == 409


class TestDisputesAPI:
    def test_create_dispute(self, api_client: TestClient, seeded_member, db_session):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.DENIED)
        db_session.commit()

        response = api_client.post(
            f"/claims/{claim.id}/disputes",
            json={"reason": "Service should be covered."},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "OPEN"
        assert data["reason"] == "Service should be covered."

    def test_list_disputes(self, api_client: TestClient, seeded_member, db_session):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.DENIED)
        db_session.commit()

        api_client.post(
            f"/claims/{claim.id}/disputes",
            json={"reason": "Please review."},
        )

        response = api_client.get(f"/claims/{claim.id}/disputes")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_create_dispute_validation_error(self, api_client: TestClient, seeded_member, db_session):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.DENIED)
        db_session.commit()

        response = api_client.post(
            f"/claims/{claim.id}/disputes",
            json={"reason": ""},
        )
        assert response.status_code == 422

    def test_create_dispute_rejects_whitespace_reason(
        self, api_client: TestClient, seeded_member, db_session
    ):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.DENIED)
        db_session.commit()

        response = api_client.post(
            f"/claims/{claim.id}/disputes",
            json={"reason": "   "},
        )
        assert response.status_code == 422

    def test_create_dispute_rejects_approved_claim(
        self, api_client: TestClient, seeded_member, db_session
    ):
        claim = create_claim(db_session, member=seeded_member, status=ClaimStatus.APPROVED)
        db_session.commit()

        response = api_client.post(
            f"/claims/{claim.id}/disputes",
            json={"reason": "This should not be allowed."},
        )
        assert response.status_code == 409
