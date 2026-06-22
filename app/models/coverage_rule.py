from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.policy import Policy


class CoverageRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coverage_rules"
    __table_args__ = (
        UniqueConstraint(
            "policy_id",
            "service_code",
            name="uq_coverage_rule_policy_service",
        ),
        CheckConstraint(
            "coverage_percentage_override IS NULL OR "
            "(coverage_percentage_override >= 0 AND coverage_percentage_override <= 1)",
            name="ck_coverage_rule_override_range",
        ),
    )

    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_covered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    coverage_percentage_override: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    policy: Mapped[Policy] = relationship(back_populates="coverage_rules")

    def __repr__(self) -> str:
        return (
            f"<CoverageRule id={self.id} service_code={self.service_code!r} "
            f"is_covered={self.is_covered}>"
        )
