"""Dispute filing and validation."""

from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.dispute import Dispute
from app.models.enums import ClaimStatus, DisputeStatus

DISPUTABLE_STATUSES = {ClaimStatus.DENIED, ClaimStatus.PARTIALLY_APPROVED}


class DisputeError(Exception):
    """Raised when a dispute cannot be created or resolved."""


def create_dispute(db: Session, *, claim: Claim, reason: str) -> Dispute:
    if not reason or not reason.strip():
        raise DisputeError("Dispute reason is required")

    if claim.status == ClaimStatus.APPROVED:
        raise DisputeError("Cannot dispute an approved claim")

    if claim.status not in DISPUTABLE_STATUSES:
        raise DisputeError(f"Cannot dispute claim with status {claim.status.value}")

    dispute = Dispute(
        claim_id=claim.id,
        reason=reason.strip(),
        status=DisputeStatus.OPEN,
    )
    db.add(dispute)
    db.flush()
    return dispute
