"""Dispute service — interface only; logic implemented in a later phase."""

from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.dispute import Dispute


class DisputeError(Exception):
    """Raised when a dispute cannot be created or resolved."""


def create_dispute(db: Session, *, claim: Claim, reason: str) -> Dispute:
    """File a dispute against a denied or partially approved claim."""
    raise NotImplementedError
