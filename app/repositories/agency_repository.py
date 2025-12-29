from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.agency import Agency
from app.models.user import ApprovalStatus, User


class AgencyRepository:
    """대행사(업체) 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, agency_id: int) -> Agency | None:
        """ID로 대행사 조회 (User 포함)

        Note: agency.id = user.id 이므로 get_by_user_id와 동일
        """
        stmt = (
            select(Agency)
            .options(joinedload(Agency.user))
            .where(Agency.id == agency_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        approval_status: Optional[ApprovalStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Agency]:
        """대행사 목록 조회"""
        stmt = select(Agency).options(joinedload(Agency.user)).join(Agency.user)

        if approval_status:
            stmt = stmt.where(User.approval_status == approval_status)

        if search:
            stmt = stmt.where(
                (User.name.ilike(f"%{search}%"))
                | (User.company_name.ilike(f"%{search}%"))
                | (User.email.ilike(f"%{search}%"))
            )

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_all(
        self,
        approval_status: Optional[ApprovalStatus] = None,
        search: Optional[str] = None,
    ) -> int:
        """대행사 수 조회"""
        stmt = select(func.count(Agency.id)).join(Agency.user)

        if approval_status:
            stmt = stmt.where(User.approval_status == approval_status)

        if search:
            stmt = stmt.where(
                (User.name.ilike(f"%{search}%"))
                | (User.company_name.ilike(f"%{search}%"))
                | (User.email.ilike(f"%{search}%"))
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, agency: Agency) -> Agency:
        """대행사 생성

        Note: agency.id는 반드시 user.id와 동일한 값으로 설정해야 함
        """
        self._session.add(agency)
        await self._session.flush()
        await self._session.refresh(agency)
        return agency

    async def delete(self, agency_id: int) -> None:
        """대행사 삭제"""
        agency = await self.get_by_id(agency_id)
        if agency:
            await self._session.delete(agency)
            await self._session.flush()
