from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser
    from app.models.agency import Agency


class RankType(str, Enum):
    """순위 추적 유형"""

    PLACE = "place"  # 플레이스 순위
    CAFE = "cafe"  # 카페 글 순위
    BLOG = "blog"  # 블로그 글 순위


class TrackingStatus(str, Enum):
    """추적 상태"""

    ACTIVE = "active"  # 추적 중
    STOPPED = "stopped"  # 추적 중단


class RankTracking(Base, TimestampMixin):
    """
    순위 추적 모델

    - type으로 place/cafe/blog 구분
    - agency가 등록하고, advertiser에게 공개
    - admin은 모든 데이터 조회 및 중단 가능
    """

    __tablename__ = "rank_trackings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 순위 유형
    type: Mapped[RankType] = mapped_column(
        SQLEnum(RankType),
        nullable=False,
        index=True,
    )

    # 업체 연결 (FK 제약 없음, 애플리케이션 레벨에서 관리)
    agency_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )  # references: agencies.id

    # 광고주 연결 (FK 제약 없음, 애플리케이션 레벨에서 관리)
    advertiser_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )  # references: advertisers.id

    # 추적 정보
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # 상태
    status: Mapped[TrackingStatus] = mapped_column(
        SQLEnum(TrackingStatus),
        nullable=False,
        default=TrackingStatus.ACTIVE,
        index=True,
    )

    # 현재 회차 (배치 로직 상태값)
    current_session: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    agency: Mapped["Agency"] = relationship(
        "Agency",
        lazy="joined",
        primaryjoin="RankTracking.agency_id == Agency.id",
        foreign_keys="RankTracking.agency_id",
    )
    advertiser: Mapped["Advertiser"] = relationship(
        "Advertiser",
        lazy="joined",
        primaryjoin="RankTracking.advertiser_id == Advertiser.id",
        foreign_keys="RankTracking.advertiser_id",
    )
    histories: Mapped[List["RankHistory"]] = relationship(
        "RankHistory",
        back_populates="tracking",
        cascade="all, delete-orphan",
        order_by="desc(RankHistory.checked_at)",
        primaryjoin="RankTracking.id == RankHistory.tracking_id",
        foreign_keys="RankHistory.tracking_id",
    )

    def __repr__(self) -> str:
        return f"<RankTracking(id={self.id}, type={self.type}, keyword={self.keyword})>"


class RankHistory(Base):
    """
    순위 히스토리 모델

    - 일일 크롤링 결과 저장
    - rank가 null이면 미노출
    - session_number는 회차 번호
    """

    __tablename__ = "rank_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 추적 연결 (FK 제약 없음, 애플리케이션 레벨에서 관리)
    tracking_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )  # references: rank_trackings.id

    # 순위 (null = 미노출)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 회차 번호
    session_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # 체크 일시
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    tracking: Mapped["RankTracking"] = relationship(
        "RankTracking",
        back_populates="histories",
        primaryjoin="RankHistory.tracking_id == RankTracking.id",
        foreign_keys="RankHistory.tracking_id",
    )

    def __repr__(self) -> str:
        return f"<RankHistory(id={self.id}, tracking_id={self.tracking_id}, rank={self.rank})>"
