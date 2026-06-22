"""Service not covered — line denied when coverage rule blocks payment."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import ClaimLineItemStatus
from app.services.adjudication import adjudicate_line_item
from tests.fixtures.domain import create_claim, create_coverage_rule, create_line_item


class TestServiceNotCovered:
    def test_denies_line_when_coverage_rule_is_not_covered(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_met,
    ):
        """A line is denied when the matching rule has is_covered=false."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="D2750",
            description="Dental crown",
            is_covered=False,
        )
        claim = create_claim(db_session, member=member_deductible_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="D2750",
            billed_amount=Decimal("1200.00"),
            description="Dental crown",
        )
        rule = standard_policy.coverage_rules[0]

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_met,
            policy=standard_policy,
            coverage_rule=rule,
        )

        assert result.status == ClaimLineItemStatus.DENIED
        assert result.approved_amount in (None, Decimal("0.00"))
        assert result.explanation is not None
        assert "not covered" in result.explanation.lower()

    def test_denies_line_when_no_coverage_rule_exists(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_met,
    ):
        """A line is denied when no coverage rule matches the service code."""
        claim = create_claim(db_session, member=member_deductible_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="UNKNOWN",
            billed_amount=Decimal("200.00"),
        )

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_met,
            policy=standard_policy,
            coverage_rule=None,
        )

        assert result.status == ClaimLineItemStatus.DENIED
        assert result.explanation is not None
        assert "not covered" in result.explanation.lower()
