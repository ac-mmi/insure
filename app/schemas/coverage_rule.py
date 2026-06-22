import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CoverageRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    policy_id: uuid.UUID
    service_code: str
    description: str
    is_covered: bool
    coverage_percentage_override: Optional[Decimal] = Field(
        default=None,
        description="Service-specific coverage rate; null uses policy default",
    )
    created_at: datetime
