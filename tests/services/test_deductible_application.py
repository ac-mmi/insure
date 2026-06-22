"""Deductible application — member share applied before insurer payment."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import ClaimLineItemStatus
from app.services.adjudication import adjudicate_line_item
from tests.fixtures.domain import create_claim, create_coverage_rule, create_line_item


class TestDeductibleApplication:
    def test_applies_deductible_before_insurer_pays(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_not_met,
    ):
        """When deductible is unmet, member share is applied first; insurer pays the remainder."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_deductible_not_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("1500.00"),
        )
        rule = standard_policy.coverage_rules[0]

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_not_met,
            policy=standard_policy,
            coverage_rule=rule,
        )

        assert result.status == ClaimLineItemStatus.APPROVED
        assert result.approved_amount == Decimal("500.00")
        assert result.explanation is not None
        assert "deductible" in result.explanation.lower()

    def test_updates_member_deductible_met(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_not_met,
    ):
        """Member deductible_met increases by the member's share of the allowed amount."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_deductible_not_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("1500.00"),
        )
        rule = standard_policy.coverage_rules[0]

        adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_not_met,
            policy=standard_policy,
            coverage_rule=rule,
        )
        db_session.refresh(member_deductible_not_met)

        assert member_deductible_not_met.deductible_met == Decimal("1000.00")

    def test_insurer_pays_nothing_when_billed_amount_within_remaining_deductible(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_not_met,
    ):
        """When the full billed amount applies to the deductible, insurer share is zero."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
        )
        claim = create_claim(db_session, member=member_deductible_not_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="99213",
            billed_amount=Decimal("800.00"),
        )
        rule = standard_policy.coverage_rules[0]

        result = adjudicate_line_item(
            db_session,
            line_item=line_item,
            member=member_deductible_not_met,
            policy=standard_policy,
            coverage_rule=rule,
        )

        assert result.status == ClaimLineItemStatus.APPROVED
        assert result.approved_amount == Decimal("0.00")
        db_session.refresh(member_deductible_not_met)
        assert member_deductible_not_met.deductible_met == Decimal("800.00")
