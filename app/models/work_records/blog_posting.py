from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser
    from app.models.agency import Agency


class BlogPosting(Base, TimestampMixin):
    """
    블로그 포스팅 기록 모델

    - 업체(Agency)가 작성한 블로그 포스팅 작업 내역
    - Agency: CRUD 가능
    - Admin: 읽기 전용
    - Advertiser: 본인 매핑 데이터만 읽기 전용
    """

    __tablename__ = "blog_postings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

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

    # 포스팅 정보
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    posting_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    agency: Mapped["Agency"] = relationship(
        "Agency",
        lazy="joined",
        primaryjoin="BlogPosting.agency_id == Agency.id",
        foreign_keys="BlogPosting.agency_id",
    )
    advertiser: Mapped["Advertiser"] = relationship(
        "Advertiser",
        lazy="joined",
        primaryjoin="BlogPosting.advertiser_id == Advertiser.id",
        foreign_keys="BlogPosting.advertiser_id",
    )

    def __repr__(self) -> str:
        return f"<BlogPosting(id={self.id}, keyword={self.keyword}, posting_date={self.posting_date})>"
