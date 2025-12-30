from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser


class CafeInfiltration(Base, TimestampMixin):
    """
    카페 침투 모델

    - Admin이 등록/관리하는 카페 침투 작업 기록
    - Admin: CRUD 가능
    - Agency: 매핑된 광고주 데이터만 읽기 전용
    - Advertiser: 본인 데이터만 읽기 전용
    """

    __tablename__ = "cafe_infiltrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 광고주 연결 (FK 제약 없음, 애플리케이션 레벨에서 관리)
    advertiser_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )  # references: advertisers.id

    # 침투 정보
    infiltration_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cafe_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    advertiser: Mapped["Advertiser"] = relationship(
        "Advertiser",
        lazy="joined",
        primaryjoin="CafeInfiltration.advertiser_id == Advertiser.id",
        foreign_keys="CafeInfiltration.advertiser_id",
    )

    def __repr__(self) -> str:
        return f"<CafeInfiltration(id={self.id}, title={self.title}, infiltration_date={self.infiltration_date})>"
