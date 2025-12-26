from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import JSON, ForeignKey
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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 사용자 연결 (1:1)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 담당 카테고리 (JSON 배열)
    categories: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agency")
    advertiser_mappings: Mapped[List["AgencyAdvertiserMapping"]] = relationship(
        "AgencyAdvertiserMapping",
        back_populates="agency",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Agency(id={self.id}, user_id={self.user_id})>"
