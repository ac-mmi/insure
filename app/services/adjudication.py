"""Adjudication service — interface only; logic implemented in a later phase."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.claim_line_item import ClaimLineItem
from app.models.coverage_rule import CoverageRule
from app.models.enums import ClaimStatus
from app.models.member import Member
from app.models.policy import Policy


class AdjudicationError(Exception):
    """Raised when a claim or line item cannot be adjudicated."""


def adjudicate_line_item(
    db: Session,
    *,
    line_item: ClaimLineItem,
    member: Member,
    policy: Policy,
    coverage_rule: Optional[CoverageRule] = None,
) -> ClaimLineItem:
    """Adjudicate a single claim line item and persist the result."""
    raise NotImplementedError


def rollup_claim_status(line_items: list[ClaimLineItem]) -> ClaimStatus:
    """Derive claim status from the adjudicated line item outcomes."""
    raise NotImplementedError


def adjudicate_claim(db: Session, claim: Claim) -> Claim:
    """Adjudicate all line items on a claim, roll up status, and persist."""
    raise NotImplementedError
