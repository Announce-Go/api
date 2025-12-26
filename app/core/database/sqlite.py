from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database.database import AbstractDatabase
from app.models.base import Base


class SQLiteDatabase(AbstractDatabase):
    """SQLite 데이터베이스 (개발/테스트용)"""

    def __init__(self, database_url: str, echo: bool = False):
        self._database_url = database_url
        self._engine = create_async_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def connect(self) -> None:
        """연결 테스트"""
        async with self._engine.begin() as conn:
            await conn.run_sync(lambda _: None)

    async def disconnect(self) -> None:
        """엔진 종료"""
        await self._engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """세션 제공"""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """테이블 생성"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
