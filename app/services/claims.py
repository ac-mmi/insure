"""Claim lifecycle operations."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.claim import Claim
from app.models.claim_line_item import ClaimLineItem
from app.models.enums import ClaimLineItemStatus, ClaimStatus
from app.models.member import Member
from app.schemas.claim import ClaimCreate
from app.services.exceptions import InvalidOperationError, NotFoundError

PAYABLE_STATUSES = {ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED}


def _load_claim(db: Session, claim_id: uuid.UUID) -> Claim:
    claim = db.scalar(
        select(Claim)
        .options(selectinload(Claim.line_items))
        .where(Claim.id == claim_id)
    )
    if claim is None:
        raise NotFoundError(f"Claim {claim_id} not found")
    return claim


def create_claim(db: Session, data: ClaimCreate) -> Claim:
    member = db.get(Member, data.member_id)
    if member is None:
        raise NotFoundError(f"Member {data.member_id} not found")

    claim = Claim(
        member_id=data.member_id,
        provider_name=data.provider_name,
        date_of_service=data.date_of_service,
        status=ClaimStatus.SUBMITTED,
        submitted_at=datetime.utcnow(),
    )
    db.add(claim)
    db.flush()

    for item in data.line_items:
        db.add(
            ClaimLineItem(
                claim_id=claim.id,
                service_code=item.service_code,
                description=item.description,
                billed_amount=item.billed_amount,
                status=ClaimLineItemStatus.PENDING,
            )
        )

    db.flush()
    db.refresh(claim)
    return _load_claim(db, claim.id)


def get_claim(db: Session, claim_id: uuid.UUID) -> Claim:
    return _load_claim(db, claim_id)


def pay_claim(db: Session, claim_id: uuid.UUID) -> Claim:
    claim = _load_claim(db, claim_id)

    if claim.status not in PAYABLE_STATUSES:
        raise InvalidOperationError(
            f"Only approved or partially approved claims can be paid; "
            f"current status is {claim.status.value}"
        )

    claim.status = ClaimStatus.PAID
    claim.paid_at = datetime.utcnow()
    db.flush()
    return claim
