import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClaimStatus
from app.schemas.claim_line_item import ClaimLineItemCreate, ClaimLineItemRead


class ClaimCreate(BaseModel):
    member_id: uuid.UUID
    provider_name: str = Field(min_length=1, max_length=255)
    date_of_service: date
    line_items: list[ClaimLineItemCreate] = Field(min_length=1)


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_id: uuid.UUID
    provider_name: str
    date_of_service: date
    status: ClaimStatus
    submitted_at: Optional[datetime] = None
    adjudicated_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    line_items: list[ClaimLineItemRead] = []
