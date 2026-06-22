"""Dispute creation — appeals allowed only for denied or partially approved claims."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session
from app.models.enums import ClaimStatus, DisputeStatus
from app.services.dispute import DisputeError, create_dispute
from tests.fixtures.domain import create_claim, create_line_item, create_member, create_policy


class TestDisputeCreation:
    def test_allows_dispute_for_denied_claim(self, db_session: Session):
        policy = create_policy(db_session)
        member = create_member(db_session, policy=policy)
        claim = create_claim(db_session, member=member, status=ClaimStatus.DENIED)
        create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("500.00"),
        )

        dispute = create_dispute(
            db_session,
            claim=claim,
            reason="I believe this service should be covered.",
        )

        assert dispute.claim_id == claim.id
        assert dispute.status == DisputeStatus.OPEN
        assert dispute.reason == "I believe this service should be covered."
        assert dispute.resolution_notes is None
        assert dispute.resolved_at is None

    def test_allows_dispute_for_partially_approved_claim(self, db_session: Session):
        policy = create_policy(db_session)
        member = create_member(db_session, policy=policy)
        claim = create_claim(
            db_session,
            member=member,
            status=ClaimStatus.PARTIALLY_APPROVED,
        )

        dispute = create_dispute(
            db_session,
            claim=claim,
            reason="The denied line item should have been approved.",
        )

        assert dispute.claim_id == claim.id
        assert dispute.status == DisputeStatus.OPEN

    def test_rejects_dispute_for_approved_claim(self, db_session: Session):
        policy = create_policy(db_session)
        member = create_member(db_session, policy=policy)
        claim = create_claim(db_session, member=member, status=ClaimStatus.APPROVED)

        with pytest.raises(DisputeError, match="(?i)approved"):
            create_dispute(
                db_session,
                claim=claim,
                reason="I want to dispute this approved claim.",
            )

    def test_rejects_dispute_for_submitted_claim(self, db_session: Session):
        policy = create_policy(db_session)
        member = create_member(db_session, policy=policy)
        claim = create_claim(db_session, member=member, status=ClaimStatus.SUBMITTED)

        with pytest.raises(DisputeError):
            create_dispute(
                db_session,
                claim=claim,
                reason="Claim has not been adjudicated yet.",
            )

    def test_rejects_dispute_for_paid_claim(self, db_session: Session):
        policy = create_policy(db_session)
        member = create_member(db_session, policy=policy)
        claim = create_claim(db_session, member=member, status=ClaimStatus.PAID)

        with pytest.raises(DisputeError):
            create_dispute(
                db_session,
                claim=claim,
                reason="Payment already issued.",
            )

    def test_rejects_empty_dispute_reason(self, db_session: Session):
        policy = create_policy(db_session)
        member = create_member(db_session, policy=policy)
        claim = create_claim(db_session, member=member, status=ClaimStatus.DENIED)

        with pytest.raises(DisputeError, match="(?i)reason"):
            create_dispute(db_session, claim=claim, reason="")
