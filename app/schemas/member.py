import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.policy import PolicyRead


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    date_of_birth: Optional[date] = None
    policy_id: uuid.UUID
    deductible_met: Decimal
    amount_paid_ytd: Decimal
    created_at: datetime
    policy: Optional[PolicyRead] = None
