import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClaimLineItemStatus


class ClaimLineItemCreate(BaseModel):
    service_code: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=255)
    billed_amount: Decimal = Field(ge=0, decimal_places=2)


class ClaimLineItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    claim_id: uuid.UUID
    service_code: str
    description: str
    billed_amount: Decimal
    approved_amount: Optional[Decimal] = None
    status: ClaimLineItemStatus
    explanation: Optional[str] = None
    created_at: datetime
