"""Annual limit exhaustion — insurer payment capped by remaining benefit."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import ClaimLineItemStatus
from app.services.adjudication import adjudicate_line_item
from tests.fixtures.domain import create_claim, create_coverage_rule, create_line_item


class TestAnnualLimitExhaustion:
    def test_caps_approved_amount_at_remaining_annual_limit(
        self,
        db_session: Session,
        standard_policy,
        member_near_annual_limit,
    ):
        """Insurer payment is reduced when it would exceed the annual limit."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_near_annual_limit)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("1000.00"),
        )
        rule = standard_policy.coverage_rules[0]

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_near_annual_limit,
            policy=standard_policy,
            coverage_rule=rule,
        )

        # 80% of 1000 = 800, but only 500 remains before hitting 10_000 limit
        assert result.status == ClaimLineItemStatus.APPROVED
        assert result.approved_amount == Decimal("500.00")
        assert result.explanation is not None
        assert "limit" in result.explanation.lower()

    def test_denies_line_when_annual_limit_fully_exhausted(
        self,
        db_session: Session,
        standard_policy,
        member_near_annual_limit,
    ):
        """A line is denied when no annual benefit remains."""
        member_near_annual_limit.amount_paid_ytd = Decimal("10000.00")
        db_session.flush()

        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_near_annual_limit)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("500.00"),
        )
        rule = standard_policy.coverage_rules[0]

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_near_annual_limit,
            policy=standard_policy,
            coverage_rule=rule,
        )

        assert result.status == ClaimLineItemStatus.DENIED
        assert result.explanation is not None
        assert "limit" in result.explanation.lower()

    def test_updates_member_amount_paid_ytd_up_to_cap(
        self,
        db_session: Session,
        standard_policy,
        member_near_annual_limit,
    ):
        """Member amount_paid_ytd reflects only the capped insurer payment."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_near_annual_limit)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("1000.00"),
        )
        rule = standard_policy.coverage_rules[0]

        adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_near_annual_limit,
            policy=standard_policy,
            coverage_rule=rule,
        )
        db_session.refresh(member_near_annual_limit)

        assert member_near_annual_limit.amount_paid_ytd == Decimal("10000.00")
