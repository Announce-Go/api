from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser
    from app.models.agency import Agency


class AgencyAdvertiserMapping(Base, TimestampMixin):
    """대행사-광고주 매핑 모델"""

    __tablename__ = "agency_advertiser_mappings"

    __table_args__ = (
        UniqueConstraint("agency_id", "advertiser_id", name="uq_agency_advertiser"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    agency_id: Mapped[int] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    advertiser_id: Mapped[int] = mapped_column(
        ForeignKey("advertisers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    agency: Mapped["Agency"] = relationship(
        "Agency", back_populates="advertiser_mappings"
    )
    advertiser: Mapped["Advertiser"] = relationship("Advertiser")

    def __repr__(self) -> str:
        return f"<AgencyAdvertiserMapping(agency_id={self.agency_id}, advertiser_id={self.advertiser_id})>"
