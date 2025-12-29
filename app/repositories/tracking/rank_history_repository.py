from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracking import RankHistory


class RankHistoryRepository:
    """순위 히스토리 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, history_id: int) -> RankHistory | None:
        """ID로 히스토리 조회"""
        stmt = select(RankHistory).where(RankHistory.id == history_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, history: RankHistory) -> RankHistory:
        """히스토리 생성"""
        self._session.add(history)
        await self._session.flush()
        await self._session.refresh(history)
        return history

    async def get_by_tracking_id(
        self,
        tracking_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RankHistory]:
        """추적 ID로 히스토리 목록 조회 (최신순)"""
        stmt = (
            select(RankHistory)
            .where(RankHistory.tracking_id == tracking_id)
            .order_by(RankHistory.checked_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_tracking_id(self, tracking_id: int) -> int:
        """추적 ID로 히스토리 개수 조회"""
        stmt = select(func.count(RankHistory.id)).where(
            RankHistory.tracking_id == tracking_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_latest_by_tracking_id(
        self,
        tracking_id: int,
    ) -> RankHistory | None:
        """추적 ID로 최신 히스토리 조회"""
        stmt = (
            select(RankHistory)
            .where(RankHistory.tracking_id == tracking_id)
            .order_by(RankHistory.checked_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_tracking_ids(
        self,
        tracking_ids: List[int],
    ) -> Dict[int, RankHistory]:
        """
        여러 추적 ID에 대한 최신 히스토리 일괄 조회

        Args:
            tracking_ids: 추적 ID 목록

        Returns:
            Dict[int, RankHistory]: tracking_id -> 최신 RankHistory 매핑
        """
        if not tracking_ids:
            return {}

        # Subquery: tracking_id별 최신 checked_at
        subq = (
            select(
                RankHistory.tracking_id,
                func.max(RankHistory.checked_at).label("max_checked_at"),
            )
            .where(RankHistory.tracking_id.in_(tracking_ids))
            .group_by(RankHistory.tracking_id)
            .subquery()
        )

        # Main query: 서브쿼리와 조인하여 실제 RankHistory 조회
        stmt = select(RankHistory).join(
            subq,
            and_(
                RankHistory.tracking_id == subq.c.tracking_id,
                RankHistory.checked_at == subq.c.max_checked_at,
            ),
        )

        result = await self._session.execute(stmt)
        histories = result.scalars().all()

        return {h.tracking_id: h for h in histories}

    async def count_exposures_in_session(
        self,
        tracking_id: int,
        session_number: int,
    ) -> int:
        """특정 회차의 노출 횟수 (rank가 null이 아닌 경우)"""
        stmt = (
            select(func.count(RankHistory.id))
            .where(RankHistory.tracking_id == tracking_id)
            .where(RankHistory.session_number == session_number)
            .where(RankHistory.rank.isnot(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_session_number(
        self,
        tracking_id: int,
        session_number: int,
    ) -> List[RankHistory]:
        """특정 회차의 히스토리 목록 조회"""
        stmt = (
            select(RankHistory)
            .where(RankHistory.tracking_id == tracking_id)
            .where(RankHistory.session_number == session_number)
            .order_by(RankHistory.checked_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        tracking_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[RankHistory]:
        """날짜 범위로 히스토리 조회"""
        stmt = (
            select(RankHistory)
            .where(RankHistory.tracking_id == tracking_id)
            .where(RankHistory.checked_at >= start_date)
            .where(RankHistory.checked_at <= end_date)
            .order_by(RankHistory.checked_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
