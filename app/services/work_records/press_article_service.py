from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_records import PressArticle
from app.repositories.agency_advertiser_mapping_repository import (
    AgencyAdvertiserMappingRepository,
)
from app.repositories.work_records import PressArticleRepository
from app.schemas.work_records.common import DailyCount
from app.schemas.work_records.press_article import (
    PressArticleCalendarResponse,
    PressArticleCreateRequest,
    PressArticleListItem,
    PressArticleUpdateRequest,
)


# 요일 한글 매핑
DAY_OF_WEEK_KO = ["월", "화", "수", "목", "금", "토", "일"]


class PressArticleService:
    """언론 기사 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._repo = PressArticleRepository(db_session)
        self._mapping_repo = AgencyAdvertiserMappingRepository(db_session)

    async def get_calendar_list_admin(
        self,
        year: int,
        month: int,
    ) -> PressArticleCalendarResponse:
        """
        언론 기사 목록 조회 (Admin용 - 전체)

        Args:
            year: 연도 (필수)
            month: 월 (필수)

        Returns:
            PressArticleCalendarResponse: 기사 목록 + daily_counts
        """
        articles = await self._repo.get_calendar_list(
            year=year,
            month=month,
        )
        daily_counts_raw = await self._repo.get_daily_counts(
            year=year,
            month=month,
        )

        return self._build_response(articles, daily_counts_raw)

    async def get_calendar_list_agency(
        self,
        agency_id: int,
        year: int,
        month: int,
    ) -> PressArticleCalendarResponse:
        """
        언론 기사 목록 조회 (Agency용 - 매핑된 광고주만)

        Args:
            agency_id: 업체 ID
            year: 연도 (필수)
            month: 월 (필수)

        Returns:
            PressArticleCalendarResponse: 기사 목록 + daily_counts
        """
        # 매핑된 광고주 ID 조회
        mappings = await self._mapping_repo.get_by_agency_id(agency_id)
        advertiser_ids = [m.advertiser_id for m in mappings]

        if not advertiser_ids:
            return PressArticleCalendarResponse(items=[], total=0, daily_counts=[])

        articles = await self._repo.get_calendar_list(
            year=year,
            month=month,
            advertiser_ids=advertiser_ids,
        )
        daily_counts_raw = await self._repo.get_daily_counts(
            year=year,
            month=month,
            advertiser_ids=advertiser_ids,
        )

        return self._build_response(articles, daily_counts_raw)

    async def get_calendar_list_advertiser(
        self,
        advertiser_id: int,
        year: int,
        month: int,
    ) -> PressArticleCalendarResponse:
        """
        언론 기사 목록 조회 (Advertiser용 - 본인만)

        Args:
            advertiser_id: 광고주 ID
            year: 연도 (필수)
            month: 월 (필수)

        Returns:
            PressArticleCalendarResponse: 기사 목록 + daily_counts
        """
        articles = await self._repo.get_calendar_list(
            year=year,
            month=month,
            advertiser_id=advertiser_id,
        )
        daily_counts_raw = await self._repo.get_daily_counts(
            year=year,
            month=month,
            advertiser_id=advertiser_id,
        )

        return self._build_response(articles, daily_counts_raw)

    async def create(
        self,
        data: PressArticleCreateRequest,
    ) -> PressArticleListItem:
        """
        언론 기사 등록 (Admin 전용)

        Args:
            data: 등록 요청 데이터

        Returns:
            PressArticleListItem: 등록된 기사
        """
        article = PressArticle(
            advertiser_id=data.advertiser_id,
            article_date=data.article_date,
            title=data.title,
            content=data.content,
            url=data.url,
        )
        article = await self._repo.create(article)
        await self._db.commit()

        # 관계 정보 로드를 위해 다시 조회
        article = await self._repo.get_by_id(article.id)

        return PressArticleListItem(
            id=article.id,
            article_date=article.article_date,
            title=article.title,
            content=article.content,
            url=article.url,
            advertiser_id=article.advertiser_id,
            advertiser_name=(
                article.advertiser.user.company_name
                if article.advertiser and article.advertiser.user
                else None
            ),
            created_at=article.created_at,
        )

    async def update(
        self,
        article_id: int,
        data: PressArticleUpdateRequest,
    ) -> Optional[PressArticleListItem]:
        """
        언론 기사 수정 (Admin 전용)

        Args:
            article_id: 기사 ID
            data: 수정 요청 데이터

        Returns:
            PressArticleListItem: 수정된 기사 (없으면 None)
        """
        article = await self._repo.get_by_id(article_id)
        if not article:
            return None

        # 필드 업데이트
        if data.article_date is not None:
            article.article_date = data.article_date
        if data.title is not None:
            article.title = data.title
        if data.content is not None:
            article.content = data.content
        if data.url is not None:
            article.url = data.url

        article = await self._repo.update(article)
        await self._db.commit()

        # 관계 정보 로드를 위해 다시 조회
        article = await self._repo.get_by_id(article.id)

        return PressArticleListItem(
            id=article.id,
            article_date=article.article_date,
            title=article.title,
            content=article.content,
            url=article.url,
            advertiser_id=article.advertiser_id,
            advertiser_name=(
                article.advertiser.user.company_name
                if article.advertiser and article.advertiser.user
                else None
            ),
            created_at=article.created_at,
        )

    async def delete(self, article_id: int) -> bool:
        """
        언론 기사 삭제 (Admin 전용)

        Args:
            article_id: 기사 ID

        Returns:
            bool: 삭제 성공 여부
        """
        article = await self._repo.get_by_id(article_id)
        if not article:
            return False

        await self._repo.delete(article)
        await self._db.commit()
        return True

    def _build_response(
        self,
        articles: List[PressArticle],
        daily_counts_raw: List[tuple],
    ) -> PressArticleCalendarResponse:
        """응답 생성"""
        items = []
        for article in articles:
            item = PressArticleListItem(
                id=article.id,
                article_date=article.article_date,
                title=article.title,
                content=article.content,
                url=article.url,
                advertiser_id=article.advertiser_id,
                advertiser_name=(
                    article.advertiser.user.company_name
                    if article.advertiser and article.advertiser.user
                    else None
                ),
                created_at=article.created_at,
            )
            items.append(item)

        daily_counts = []
        for article_date, count in daily_counts_raw:
            day_of_week = DAY_OF_WEEK_KO[article_date.weekday()]
            daily_counts.append(
                DailyCount(
                    date=article_date.isoformat(),
                    day_of_week=day_of_week,
                    count=count,
                )
            )

        return PressArticleCalendarResponse(
            items=items,
            total=len(items),
            daily_counts=daily_counts,
        )
