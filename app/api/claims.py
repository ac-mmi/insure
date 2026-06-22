import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models.claim import Claim
from app.models.enums import ClaimStatus
from app.schemas.claim import ClaimCreate, ClaimRead
from app.schemas.dispute import DisputeCreate, DisputeRead
from app.services.adjudication import adjudicate_claim
from app.services.claims import create_claim, get_claim, pay_claim
from app.services.dispute import create_dispute
from app.services.exceptions import InvalidOperationError, NotFoundError

router = APIRouter(prefix="/claims", tags=["claims"])


def _load_claim_with_disputes(db: Session, claim_id: uuid.UUID) -> Claim:
    claim = db.scalar(
        select(Claim)
        .options(selectinload(Claim.line_items), selectinload(Claim.disputes))
        .where(Claim.id == claim_id)
    )
    if claim is None:
        raise NotFoundError(f"Claim {claim_id} not found")
    return claim


@router.post("", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
def submit_claim(data: ClaimCreate, db: Session = Depends(get_db)) -> Claim:
    claim = create_claim(db, data)
    db.commit()
    return claim


@router.get("/{claim_id}", response_model=ClaimRead)
def retrieve_claim(claim_id: uuid.UUID, db: Session = Depends(get_db)) -> Claim:
    claim = get_claim(db, claim_id)
    return claim


@router.post("/{claim_id}/adjudicate", response_model=ClaimRead)
def adjudicate_claim_endpoint(
    claim_id: uuid.UUID, db: Session = Depends(get_db)
) -> Claim:
    claim = get_claim(db, claim_id)

    if claim.status != ClaimStatus.SUBMITTED:
        raise InvalidOperationError(
            f"Only submitted claims can be adjudicated; current status is {claim.status.value}"
        )

    adjudicate_claim(db, claim)
    db.commit()
    return get_claim(db, claim_id)


@router.post("/{claim_id}/pay", response_model=ClaimRead)
def pay_claim_endpoint(claim_id: uuid.UUID, db: Session = Depends(get_db)) -> Claim:
    claim = pay_claim(db, claim_id)
    db.commit()
    return claim


@router.post(
    "/{claim_id}/disputes",
    response_model=DisputeRead,
    status_code=status.HTTP_201_CREATED,
)
def file_dispute(
    claim_id: uuid.UUID,
    data: DisputeCreate,
    db: Session = Depends(get_db),
) -> DisputeRead:
    claim = get_claim(db, claim_id)
    dispute = create_dispute(db, claim=claim, reason=data.reason)
    db.commit()
    db.refresh(dispute)
    return dispute


@router.get("/{claim_id}/disputes", response_model=list[DisputeRead])
def list_disputes(claim_id: uuid.UUID, db: Session = Depends(get_db)) -> list:
    claim = _load_claim_with_disputes(db, claim_id)
    return claim.disputes
