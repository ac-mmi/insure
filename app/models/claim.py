from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ClaimStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.claim_line_item import ClaimLineItem
    from app.models.dispute import Dispute
    from app.models.member import Member


class Claim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "claims"

    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_service: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, native_enum=False),
        nullable=False,
        default=ClaimStatus.SUBMITTED,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    adjudicated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    member: Mapped[Member] = relationship(back_populates="claims")
    line_items: Mapped[list[ClaimLineItem]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
        order_by="ClaimLineItem.created_at",
    )
    disputes: Mapped[list[Dispute]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Claim id={self.id} status={self.status.value}>"
