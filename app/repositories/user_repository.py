from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """사용자 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """ID로 사용자 조회"""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login_id(self, login_id: str) -> User | None:
        """로그인 ID로 사용자 조회"""
        stmt = select(User).where(User.login_id == login_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """이메일로 사용자 조회"""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """사용자 생성"""
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def exists_by_login_id(self, login_id: str) -> bool:
        """로그인 ID 존재 여부"""
        stmt = select(User.id).where(User.login_id == login_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_email(self, email: str) -> bool:
        """이메일 존재 여부"""
        stmt = select(User.id).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
