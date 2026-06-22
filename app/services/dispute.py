"""Dispute filing and validation."""

from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.dispute import Dispute
from app.models.enums import ClaimStatus, DisputeStatus
from app.services.exceptions import StateConflictError

DISPUTABLE_STATUSES = {ClaimStatus.DENIED, ClaimStatus.PARTIALLY_APPROVED}


class DisputeError(Exception):
    """Raised when a dispute cannot be created due to invalid input."""


def create_dispute(db: Session, *, claim: Claim, reason: str) -> Dispute:
    stripped_reason = reason.strip() if reason else ""
    if not stripped_reason:
        raise DisputeError("Dispute reason is required")

    if claim.status == ClaimStatus.APPROVED:
        raise StateConflictError("Cannot dispute an approved claim")

    if claim.status not in DISPUTABLE_STATUSES:
        raise StateConflictError(
            f"Cannot dispute claim with status {claim.status.value}"
        )

    dispute = Dispute(
        claim_id=claim.id,
        reason=stripped_reason,
        status=DisputeStatus.OPEN,
    )
    db.add(dispute)
    db.flush()
    return dispute
