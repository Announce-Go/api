from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AgencyCategory(str, Enum):
    """업체 이용 카테고리 (기능 접근 권한 결정)"""

    PLACE_RANK = "place_rank"  # 플레이스 순위
    CAFE_RANK = "cafe_rank"  # 카페 글 순위
    BLOG_RANK = "blog_rank"  # 블로그 글 순위
    BLOG_POSTING = "blog_posting"  # 블로그 포스팅 기록
    NEWS_ARTICLE = "news_article"  # 언론 기사
    CAFE_INFILTRATION = "cafe_infiltration"  # 카페 침투

if TYPE_CHECKING:
    from app.models.agency_advertiser_mapping import AgencyAdvertiserMapping
    from app.models.user import User


class Agency(Base, TimestampMixin):
    """대행사(업체) 모델"""

    __tablename__ = "agencies"

    # PK = user.id (auto-increment 없음)
    id: Mapped[int] = mapped_column(primary_key=True)  # references: users.id

    # 담당 카테고리 (JSON 배열)
    categories: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="agency",
        primaryjoin="Agency.id == User.id",
        foreign_keys="Agency.id",
    )
    advertiser_mappings: Mapped[List["AgencyAdvertiserMapping"]] = relationship(
        "AgencyAdvertiserMapping",
        back_populates="agency",
        cascade="all, delete-orphan",
        primaryjoin="Agency.id == AgencyAdvertiserMapping.agency_id",
        foreign_keys="AgencyAdvertiserMapping.agency_id",
    )

    def __repr__(self) -> str:
        return f"<Agency(id={self.id})>"
