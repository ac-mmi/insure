"""Claim and line-item adjudication."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.claim_line_item import ClaimLineItem
from app.models.coverage_rule import CoverageRule
from app.models.enums import ClaimLineItemStatus, ClaimStatus
from app.models.member import Member
from app.models.policy import Policy
from app.services.exceptions import StateConflictError

NOT_COVERED_EXPLANATION = "Service not covered under policy"
ANNUAL_LIMIT_EXPLANATION = "Annual benefit limit reached"


class AdjudicationError(Exception):
    """Raised when a claim or line item cannot be adjudicated."""


def _money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"))


def _get_coverage_percentage(policy: Policy, coverage_rule: CoverageRule) -> Decimal:
    if coverage_rule.coverage_percentage_override is not None:
        return coverage_rule.coverage_percentage_override
    return policy.coverage_percentage


def _deny_line_item(line_item: ClaimLineItem, explanation: str) -> ClaimLineItem:
    line_item.status = ClaimLineItemStatus.DENIED
    line_item.approved_amount = Decimal("0.00")
    line_item.explanation = explanation
    return line_item


def _approve_line_item(
    line_item: ClaimLineItem,
    insurer_payment: Decimal,
    explanation: str,
) -> ClaimLineItem:
    line_item.status = ClaimLineItemStatus.APPROVED
    line_item.approved_amount = _money(insurer_payment)
    line_item.explanation = explanation
    return line_item


def _build_coverage_explanation(coverage_rule: CoverageRule, policy: Policy) -> str:
    if coverage_rule.coverage_percentage_override is not None:
        pct = int(coverage_rule.coverage_percentage_override * 100)
        return f"Covered service. {pct}% override applied."
    pct = int(policy.coverage_percentage * 100)
    return f"Covered service. {pct}% coverage applied."


def adjudicate_line_item(
    db: Session,
    *,
    line_item: ClaimLineItem,
    member: Member,
    policy: Policy,
    coverage_rule: Optional[CoverageRule] = None,
) -> ClaimLineItem:
    if coverage_rule is None or not coverage_rule.is_covered:
        _deny_line_item(line_item, NOT_COVERED_EXPLANATION)
        db.flush()
        return line_item

    billed_amount = line_item.billed_amount
    remaining_limit = policy.annual_limit - member.amount_paid_ytd

    if remaining_limit <= 0:
        _deny_line_item(line_item, ANNUAL_LIMIT_EXPLANATION)
        db.flush()
        return line_item

    if member.deductible_met < policy.deductible:
        remaining_deductible = policy.deductible - member.deductible_met
        member_share = min(billed_amount, remaining_deductible)
        member.deductible_met = _money(member.deductible_met + member_share)
        insurer_payment = billed_amount - member_share
        explanation = (
            f"Covered service. Deductible applied: ${member_share} toward deductible."
        )
    else:
        coverage_pct = _get_coverage_percentage(policy, coverage_rule)
        insurer_payment = billed_amount * coverage_pct
        explanation = _build_coverage_explanation(coverage_rule, policy)

    if insurer_payment > remaining_limit:
        insurer_payment = remaining_limit
        explanation = f"{explanation} Payment capped at annual limit."

    insurer_payment = _money(insurer_payment)

    _approve_line_item(line_item, insurer_payment, explanation)
    member.amount_paid_ytd = _money(member.amount_paid_ytd + insurer_payment)

    db.flush()
    return line_item


def rollup_claim_status(line_items: list[ClaimLineItem]) -> ClaimStatus:
    if any(item.status == ClaimLineItemStatus.PENDING for item in line_items):
        raise AdjudicationError("Cannot rollup claim with pending line items")

    statuses = {item.status for item in line_items}

    if statuses == {ClaimLineItemStatus.APPROVED}:
        return ClaimStatus.APPROVED
    if statuses == {ClaimLineItemStatus.DENIED}:
        return ClaimStatus.DENIED
    return ClaimStatus.PARTIALLY_APPROVED


def _find_coverage_rule(
    db: Session,
    policy_id,
    service_code: str,
) -> Optional[CoverageRule]:
    return db.scalar(
        select(CoverageRule).where(
            CoverageRule.policy_id == policy_id,
            CoverageRule.service_code == service_code,
        )
    )


def adjudicate_claim(db: Session, claim: Claim) -> Claim:
    if claim.status != ClaimStatus.SUBMITTED:
        raise StateConflictError(
            f"Only submitted claims can be adjudicated; current status is {claim.status.value}"
        )

    member = claim.member
    if member is None:
        member = db.get(Member, claim.member_id)
    if member is None:
        raise AdjudicationError("Claim member not found")

    policy = member.policy
    if policy is None:
        policy = db.get(Policy, member.policy_id)
    if policy is None:
        raise AdjudicationError("Member policy not found")

    claim.status = ClaimStatus.UNDER_REVIEW

    for line_item in claim.line_items:
        coverage_rule = _find_coverage_rule(db, policy.id, line_item.service_code)
        adjudicate_line_item(
            db,
            line_item=line_item,
            member=member,
            policy=policy,
            coverage_rule=coverage_rule,
        )

    claim.status = rollup_claim_status(claim.line_items)
    claim.adjudicated_at = datetime.utcnow()
    db.flush()
    return claim
