from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ClaimLineItemStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.claim import Claim


class ClaimLineItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "claim_line_items"
    __table_args__ = (
        CheckConstraint("billed_amount >= 0", name="ck_line_item_billed_amount_non_negative"),
        CheckConstraint(
            "approved_amount IS NULL OR approved_amount >= 0",
            name="ck_line_item_approved_amount_non_negative",
        ),
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    billed_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[ClaimLineItemStatus] = mapped_column(
        Enum(ClaimLineItemStatus, native_enum=False),
        nullable=False,
        default=ClaimLineItemStatus.PENDING,
    )
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    claim: Mapped[Claim] = relationship(back_populates="line_items")

    def __repr__(self) -> str:
        return (
            f"<ClaimLineItem id={self.id} service_code={self.service_code!r} "
            f"status={self.status.value}>"
        )
