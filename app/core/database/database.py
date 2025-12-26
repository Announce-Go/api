from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncGenerator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AbstractDatabase(ABC):
    """데이터베이스 추상 클래스"""

    @abstractmethod
    async def connect(self) -> None:
        """데이터베이스 연결"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """데이터베이스 연결 해제"""
        pass

    @abstractmethod
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        비동기 세션 제공 (FastAPI Depends용)

        Yields:
            AsyncSession: SQLAlchemy 비동기 세션
        """
        pass

    @abstractmethod
    async def create_tables(self) -> None:
        """
        모든 테이블 생성 (개발용)

        운영에서는 Alembic 마이그레이션 사용 권장
        """
        pass
