from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.policy import Policy


class Member(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "members"
    __table_args__ = (
        CheckConstraint("deductible_met >= 0", name="ck_member_deductible_met_non_negative"),
        CheckConstraint("amount_paid_ytd >= 0", name="ck_member_amount_paid_ytd_non_negative"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("policies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    deductible_met: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    amount_paid_ytd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    policy: Mapped[Policy] = relationship(back_populates="members")
    claims: Mapped[list[Claim]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Member id={self.id} name={self.name!r}>"
