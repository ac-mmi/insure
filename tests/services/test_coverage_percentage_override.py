"""Coverage percentage override — service-specific rate takes precedence over policy default."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import ClaimLineItemStatus
from app.services.adjudication import adjudicate_line_item
from tests.fixtures.domain import create_claim, create_coverage_rule, create_line_item


class TestCoveragePercentageOverride:
    def test_override_takes_precedence_over_policy_default(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_met,
    ):
        """When a rule defines coverage_percentage_override, it replaces the policy default."""
        assert standard_policy.coverage_percentage == Decimal("0.80")

        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="92004",
            description="Vision exam",
            is_covered=True,
            coverage_percentage_override=Decimal("0.90"),
        )
        claim = create_claim(db_session, member=member_deductible_met)
        line_item = create_line_item(
            db_session,
            claim=claim,
            service_code="92004",
            billed_amount=Decimal("1000.00"),
            description="Vision exam",
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
        assert result.approved_amount == Decimal("900.00")  # 1000 * 90%, not 80%
        assert result.explanation is not None

    def test_policy_default_used_when_override_is_null(
        self,
        db_session: Session,
        standard_policy,
        member_deductible_met,
    ):
        """When override is null, adjudication falls back to policy.coverage_percentage."""
        create_coverage_rule(
            db_session,
            policy=standard_policy,
            service_code="99213",
            is_covered=True,
            coverage_percentage_override=None,
        )
        claim = create_claim(db_session, member=member_deductible_met)
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
            member=member_deductible_met,
            policy=standard_policy,
            coverage_rule=rule,
        )

        assert result.approved_amount == Decimal("800.00")  # 1000 * 80%
