import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    deductible: Decimal
    coverage_percentage: Decimal = Field(description="Insurer share after deductible (0.0–1.0)")
    annual_limit: Decimal
    created_at: datetime
