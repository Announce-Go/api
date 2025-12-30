from __future__ import annotations

import calendar
from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.advertiser import Advertiser
from app.models.work_records import PressArticle


class PressArticleRepository:
    """언론 기사 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, article_id: int) -> PressArticle | None:
        """ID로 기사 조회"""
        stmt = (
            select(PressArticle)
            .options(
                joinedload(PressArticle.advertiser).joinedload(Advertiser.user),
            )
            .where(PressArticle.id == article_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, article: PressArticle) -> PressArticle:
        """기사 생성"""
        self._session.add(article)
        await self._session.flush()
        await self._session.refresh(article)
        return article

    async def update(self, article: PressArticle) -> PressArticle:
        """기사 업데이트"""
        await self._session.flush()
        await self._session.refresh(article)
        return article

    async def delete(self, article: PressArticle) -> None:
        """기사 삭제"""
        await self._session.delete(article)
        await self._session.flush()

    async def get_calendar_list(
        self,
        year: int,
        month: int,
        advertiser_id: Optional[int] = None,
        advertiser_ids: Optional[List[int]] = None,
    ) -> List[PressArticle]:
        """
        캘린더용 기사 목록 조회 (페이지네이션 없음)

        Args:
            year: 연도 (필수)
            month: 월 (필수)
            advertiser_id: 광고주 필터 (단일)
            advertiser_ids: 광고주 필터 (다중, 업체용)
        """
        stmt = select(PressArticle).options(
            joinedload(PressArticle.advertiser).joinedload(Advertiser.user),
        )

        if advertiser_id:
            stmt = stmt.where(PressArticle.advertiser_id == advertiser_id)

        if advertiser_ids:
            stmt = stmt.where(PressArticle.advertiser_id.in_(advertiser_ids))

        # 연월 필터 (필수)
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        stmt = stmt.where(PressArticle.article_date.between(start_date, end_date))

        stmt = stmt.order_by(PressArticle.article_date.desc())
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
        날짜별 기사 개수 조회 (캘린더 UI용)

        Returns:
            List of (date, count) tuples
        """
        stmt = select(
            PressArticle.article_date,
            func.count(PressArticle.id).label("count"),
        )

        if advertiser_id:
            stmt = stmt.where(PressArticle.advertiser_id == advertiser_id)

        if advertiser_ids:
            stmt = stmt.where(PressArticle.advertiser_id.in_(advertiser_ids))

        # 연월 필터 (필수)
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        stmt = stmt.where(PressArticle.article_date.between(start_date, end_date))

        stmt = stmt.group_by(PressArticle.article_date).order_by(
            PressArticle.article_date
        )
        result = await self._session.execute(stmt)
        return [(row.article_date, row.count) for row in result.all()]

    async def count(
        self,
        advertiser_id: Optional[int] = None,
        advertiser_ids: Optional[List[int]] = None,
    ) -> int:
        """기사 개수 조회"""
        stmt = select(func.count(PressArticle.id))

        if advertiser_id:
            stmt = stmt.where(PressArticle.advertiser_id == advertiser_id)

        if advertiser_ids:
            stmt = stmt.where(PressArticle.advertiser_id.in_(advertiser_ids))

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_by_advertiser_id(self, advertiser_id: int) -> int:
        """advertiser_id가 일치하는 모든 기사 삭제

        Note: CASCADE DELETE 대체용 (애플리케이션 레벨 삭제)
        """
        stmt = select(PressArticle).where(PressArticle.advertiser_id == advertiser_id)
        result = await self._session.execute(stmt)
        articles = list(result.scalars().all())

        for article in articles:
            await self._session.delete(article)

        await self._session.flush()
        return len(articles)
