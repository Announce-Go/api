from __future__ import annotations

import calendar
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.advertiser import Advertiser
from app.models.work_records import CafeInfiltration


class CafeInfiltrationRepository:
    """카페 침투 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, infiltration_id: int) -> CafeInfiltration | None:
        """ID로 침투 기록 조회"""
        stmt = (
            select(CafeInfiltration)
            .options(
                joinedload(CafeInfiltration.advertiser).joinedload(Advertiser.user),
            )
            .where(CafeInfiltration.id == infiltration_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, infiltration: CafeInfiltration) -> CafeInfiltration:
        """침투 기록 생성"""
        self._session.add(infiltration)
        await self._session.flush()
        await self._session.refresh(infiltration)
        return infiltration

    async def update(self, infiltration: CafeInfiltration) -> CafeInfiltration:
        """침투 기록 업데이트"""
        await self._session.flush()
        await self._session.refresh(infiltration)
        return infiltration

    async def delete(self, infiltration: CafeInfiltration) -> None:
        """침투 기록 삭제"""
        await self._session.delete(infiltration)
        await self._session.flush()

    async def get_calendar_list(
        self,
        year: int,
        month: int,
        advertiser_id: Optional[int] = None,
        advertiser_ids: Optional[List[int]] = None,
    ) -> List[CafeInfiltration]:
        """
        캘린더용 침투 목록 조회 (페이지네이션 없음)

        Args:
            year: 연도 (필수)
            month: 월 (필수)
            advertiser_id: 광고주 필터 (단일)
            advertiser_ids: 광고주 필터 (다중, 업체용)
        """
        stmt = select(CafeInfiltration).options(
            joinedload(CafeInfiltration.advertiser).joinedload(Advertiser.user),
        )

        if advertiser_id:
            stmt = stmt.where(CafeInfiltration.advertiser_id == advertiser_id)

        if advertiser_ids:
            stmt = stmt.where(CafeInfiltration.advertiser_id.in_(advertiser_ids))

        # 연월 필터 (필수)
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        stmt = stmt.where(
            CafeInfiltration.infiltration_date.between(start_date, end_date)
        )

        stmt = stmt.order_by(CafeInfiltration.infiltration_date.desc())
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_daily_counts(
        self,
        year: int,
        month: int,
        advertiser_id: Optional[int] = None,
        advertiser_ids: Optional[List[int]] = None,
    ) -> List[Tuple[date, int]]:
        """
        날짜별 침투 개수 조회 (캘린더 UI용)

        Returns:
            List of (date, count) tuples
        """
        stmt = select(
            CafeInfiltration.infiltration_date,
            func.count(CafeInfiltration.id).label("count"),
        )

        if advertiser_id:
            stmt = stmt.where(CafeInfiltration.advertiser_id == advertiser_id)

        if advertiser_ids:
            stmt = stmt.where(CafeInfiltration.advertiser_id.in_(advertiser_ids))

        # 연월 필터 (필수)
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        stmt = stmt.where(
            CafeInfiltration.infiltration_date.between(start_date, end_date)
        )

        stmt = stmt.group_by(CafeInfiltration.infiltration_date).order_by(
            CafeInfiltration.infiltration_date
        )
        result = await self._session.execute(stmt)
        return [(row.infiltration_date, row.count) for row in result.all()]

    async def count(
        self,
        advertiser_id: Optional[int] = None,
        advertiser_ids: Optional[List[int]] = None,
    ) -> int:
        """침투 개수 조회"""
        stmt = select(func.count(CafeInfiltration.id))

        if advertiser_id:
            stmt = stmt.where(CafeInfiltration.advertiser_id == advertiser_id)

        if advertiser_ids:
            stmt = stmt.where(CafeInfiltration.advertiser_id.in_(advertiser_ids))

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_by_advertiser_id(self, advertiser_id: int) -> int:
        """advertiser_id가 일치하는 모든 침투 기록 삭제

        Note: CASCADE DELETE 대체용 (애플리케이션 레벨 삭제)
        """
        stmt = select(CafeInfiltration).where(
            CafeInfiltration.advertiser_id == advertiser_id
        )
        result = await self._session.execute(stmt)
        infiltrations = list(result.scalars().all())

        for infiltration in infiltrations:
            await self._session.delete(infiltration)

        await self._session.flush()
        return len(infiltrations)
