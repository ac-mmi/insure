"""Covered service approval — insurer pays after deductible is met."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import ClaimLineItemStatus
from app.services.adjudication import adjudicate_line_item
from tests.fixtures.domain import create_claim, create_coverage_rule, create_line_item


class TestCoveredServiceApproval:
    def test_approves_line_when_deductible_met_and_coverage_applies(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_met,
    ):
        """A covered service with met deductible is approved at the policy coverage rate."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            description="Office visit",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_deductible_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("500.00"),
            description="Office visit",
        )
        rule = standard_policy.coverage_rules[0]

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_met,
            policy=standard_policy,
            coverage_rule=rule,
        )

        assert result.status == ClaimLineItemStatus.APPROVED
        assert result.approved_amount == Decimal("400.00")  # 500 * 80%
        assert result.explanation is not None
        assert len(result.explanation) > 0

    def test_updates_member_amount_paid_ytd(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_met,
    ):
        """Approved insurer payment increments the member's year-to-date total."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_deductible_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("500.00"),
        )
        rule = standard_policy.coverage_rules[0]
        initial_paid = member_deductible_met.amount_paid_ytd

        adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_met,
            policy=standard_policy,
            coverage_rule=rule,
        )
        db_session.refresh(member_deductible_met)

        assert member_deductible_met.amount_paid_ytd == initial_paid + Decimal("400.00")
