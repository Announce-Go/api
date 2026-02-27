from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, func, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

KST = ZoneInfo("Asia/Seoul")


class KSTDateTime(types.TypeDecorator):
    """DB에서 읽을 때 자동으로 Asia/Seoul로 변환하는 DateTime 타입"""

    impl = DateTime
    cache_ok = True

    def __init__(self) -> None:
        super().__init__(timezone=True)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=ZoneInfo("UTC"))
        return value.astimezone(KST)

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        return value


class Base(DeclarativeBase):
    """모든 모델의 기본 클래스"""

    pass


class TimestampMixin:
    """생성/수정 시간 Mixin"""

    created_at: Mapped[datetime] = mapped_column(
        KSTDateTime(),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        KSTDateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
