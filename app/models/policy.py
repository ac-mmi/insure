from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.coverage_rule import CoverageRule
    from app.models.member import Member


class Policy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "policies"
    __table_args__ = (
        CheckConstraint("deductible >= 0", name="ck_policy_deductible_non_negative"),
        CheckConstraint(
            "coverage_percentage >= 0 AND coverage_percentage <= 1",
            name="ck_policy_coverage_percentage_range",
        ),
        CheckConstraint("annual_limit >= 0", name="ck_policy_annual_limit_non_negative"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    deductible: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    coverage_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    annual_limit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    members: Mapped[list[Member]] = relationship(back_populates="policy")
    coverage_rules: Mapped[list[CoverageRule]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Policy id={self.id} name={self.name!r}>"
