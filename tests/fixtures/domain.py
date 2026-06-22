from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.claim_line_item import ClaimLineItem
from app.models.coverage_rule import CoverageRule
from app.models.enums import ClaimLineItemStatus, ClaimStatus
from app.models.member import Member
from app.models.policy import Policy


def create_policy(
    session: Session,
    *,
    name: str = "Gold PPO 2026",
    deductible: Decimal = Decimal("1000.00"),
    coverage_percentage: Decimal = Decimal("0.80"),
    annual_limit: Decimal = Decimal("10000.00"),
) -> Policy:
    policy = Policy(
        name=name,
        deductible=deductible,
        coverage_percentage=coverage_percentage,
        annual_limit=annual_limit,
    )
    session.add(policy)
    session.flush()
    return policy


def create_member(
    session: Session,
    *,
    policy: Policy,
    name: str = "Jane Doe",
    deductible_met: Decimal = Decimal("0.00"),
    amount_paid_ytd: Decimal = Decimal("0.00"),
) -> Member:
    member = Member(
        name=name,
        policy_id=policy.id,
        deductible_met=deductible_met,
        amount_paid_ytd=amount_paid_ytd,
    )
    session.add(member)
    session.flush()
    return member


def create_coverage_rule(
    session: Session,
    *,
    policy: Policy,
    service_code: str,
    description: str = "Medical service",
    is_covered: bool = True,
    coverage_percentage_override: Optional[Decimal] = None,
) -> CoverageRule:
    rule = CoverageRule(
        policy_id=policy.id,
        service_code=service_code,
        description=description,
        is_covered=is_covered,
        coverage_percentage_override=coverage_percentage_override,
    )
    session.add(rule)
    session.flush()
    return rule


def create_claim(
    session: Session,
    *,
    member: Member,
    provider_name: str = "City Medical Center",
    status: ClaimStatus = ClaimStatus.SUBMITTED,
) -> Claim:
    from datetime import date

    claim = Claim(
        member_id=member.id,
        provider_name=provider_name,
        date_of_service=date(2026, 3, 15),
        status=status,
    )
    session.add(claim)
    session.flush()
    return claim


def create_line_item(
    session: Session,
    *,
    claim: Claim,
    service_code: str,
    billed_amount: Decimal,
    description: str = "Medical service",
    status: ClaimLineItemStatus = ClaimLineItemStatus.PENDING,
) -> ClaimLineItem:
    line_item = ClaimLineItem(
        claim_id=claim.id,
        service_code=service_code,
        description=description,
        billed_amount=billed_amount,
        status=status,
    )
    session.add(line_item)
    session.flush()
    return line_item
