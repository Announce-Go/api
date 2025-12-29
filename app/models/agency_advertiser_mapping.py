from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser
    from app.models.agency import Agency


class AgencyAdvertiserMapping(Base, TimestampMixin):
    """대행사-광고주 매핑 모델"""

    __tablename__ = "agency_advertiser_mappings"

    # 복합 Primary Key (FK 제약 없음)
    agency_id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )  # references: agencies.id
    advertiser_id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )  # references: advertisers.id

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    agency: Mapped["Agency"] = relationship(
        "Agency",
        back_populates="advertiser_mappings",
        primaryjoin="AgencyAdvertiserMapping.agency_id == Agency.id",
        foreign_keys="AgencyAdvertiserMapping.agency_id",
    )
    advertiser: Mapped["Advertiser"] = relationship(
        "Advertiser",
        primaryjoin="AgencyAdvertiserMapping.advertiser_id == Advertiser.id",
        foreign_keys="AgencyAdvertiserMapping.advertiser_id",
    )

    def __repr__(self) -> str:
        return f"<AgencyAdvertiserMapping(agency_id={self.agency_id}, advertiser_id={self.advertiser_id})>"
