from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_records import CafeInfiltration
from app.repositories.agency_advertiser_mapping_repository import (
    AgencyAdvertiserMappingRepository,
)
from app.repositories.work_records import CafeInfiltrationRepository
from app.schemas.work_records.cafe_infiltration import (
    CafeInfiltrationCalendarResponse,
    CafeInfiltrationCreateRequest,
    CafeInfiltrationListItem,
    CafeInfiltrationUpdateRequest,
)
from app.schemas.work_records.common import DailyCount


# 요일 한글 매핑
DAY_OF_WEEK_KO = ["월", "화", "수", "목", "금", "토", "일"]


class CafeInfiltrationService:
    """카페 침투 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._repo = CafeInfiltrationRepository(db_session)
        self._mapping_repo = AgencyAdvertiserMappingRepository(db_session)

    async def get_calendar_list_admin(
        self,
        year: int,
        month: int,
    ) -> CafeInfiltrationCalendarResponse:
        """
        카페 침투 목록 조회 (Admin용 - 전체)

        Args:
            year: 연도 (필수)
            month: 월 (필수)

        Returns:
            CafeInfiltrationCalendarResponse: 침투 목록 + daily_counts
        """
        infiltrations = await self._repo.get_calendar_list(
            year=year,
            month=month,
        )
        daily_counts_raw = await self._repo.get_daily_counts(
            year=year,
            month=month,
        )

        return self._build_response(infiltrations, daily_counts_raw)

    async def get_calendar_list_agency(
        self,
        agency_id: int,
        year: int,
        month: int,
    ) -> CafeInfiltrationCalendarResponse:
        """
        카페 침투 목록 조회 (Agency용 - 매핑된 광고주만)

        Args:
            agency_id: 업체 ID
            year: 연도 (필수)
            month: 월 (필수)

        Returns:
            CafeInfiltrationCalendarResponse: 침투 목록 + daily_counts
        """
        # 매핑된 광고주 ID 조회
        mappings = await self._mapping_repo.get_by_agency_id(agency_id)
        advertiser_ids = [m.advertiser_id for m in mappings]

        if not advertiser_ids:
            return CafeInfiltrationCalendarResponse(items=[], total=0, daily_counts=[])

        infiltrations = await self._repo.get_calendar_list(
            year=year,
            month=month,
            advertiser_ids=advertiser_ids,
        )
        daily_counts_raw = await self._repo.get_daily_counts(
            year=year,
            month=month,
            advertiser_ids=advertiser_ids,
        )

        return self._build_response(infiltrations, daily_counts_raw)

    async def get_calendar_list_advertiser(
        self,
        advertiser_id: int,
        year: int,
        month: int,
    ) -> CafeInfiltrationCalendarResponse:
        """
        카페 침투 목록 조회 (Advertiser용 - 본인만)

        Args:
            advertiser_id: 광고주 ID
            year: 연도 (필수)
            month: 월 (필수)

        Returns:
            CafeInfiltrationCalendarResponse: 침투 목록 + daily_counts
        """
        infiltrations = await self._repo.get_calendar_list(
            year=year,
            month=month,
            advertiser_id=advertiser_id,
        )
        daily_counts_raw = await self._repo.get_daily_counts(
            year=year,
            month=month,
            advertiser_id=advertiser_id,
        )

        return self._build_response(infiltrations, daily_counts_raw)

    async def create(
        self,
        data: CafeInfiltrationCreateRequest,
    ) -> CafeInfiltrationListItem:
        """
        카페 침투 등록 (Admin 전용)

        Args:
            data: 등록 요청 데이터

        Returns:
            CafeInfiltrationListItem: 등록된 침투 기록
        """
        infiltration = CafeInfiltration(
            advertiser_id=data.advertiser_id,
            infiltration_date=data.infiltration_date,
            title=data.title,
            content=data.content,
            cafe_name=data.cafe_name,
            url=data.url,
        )
        infiltration = await self._repo.create(infiltration)
        await self._db.commit()

        # 관계 정보 로드를 위해 다시 조회
        infiltration = await self._repo.get_by_id(infiltration.id)

        return CafeInfiltrationListItem(
            id=infiltration.id,
            infiltration_date=infiltration.infiltration_date,
            title=infiltration.title,
            content=infiltration.content,
            cafe_name=infiltration.cafe_name,
            url=infiltration.url,
            advertiser_id=infiltration.advertiser_id,
            advertiser_name=(
                infiltration.advertiser.user.company_name
                if infiltration.advertiser and infiltration.advertiser.user
                else None
            ),
            created_at=infiltration.created_at,
        )

    async def update(
        self,
        infiltration_id: int,
        data: CafeInfiltrationUpdateRequest,
    ) -> Optional[CafeInfiltrationListItem]:
        """
        카페 침투 수정 (Admin 전용)

        Args:
            infiltration_id: 침투 ID
            data: 수정 요청 데이터

        Returns:
            CafeInfiltrationListItem: 수정된 침투 기록 (없으면 None)
        """
        infiltration = await self._repo.get_by_id(infiltration_id)
        if not infiltration:
            return None

        # 필드 업데이트
        if data.infiltration_date is not None:
            infiltration.infiltration_date = data.infiltration_date
        if data.title is not None:
            infiltration.title = data.title
        if data.content is not None:
            infiltration.content = data.content
        if data.cafe_name is not None:
            infiltration.cafe_name = data.cafe_name
        if data.url is not None:
            infiltration.url = data.url

        infiltration = await self._repo.update(infiltration)
        await self._db.commit()

        # 관계 정보 로드를 위해 다시 조회
        infiltration = await self._repo.get_by_id(infiltration.id)

        return CafeInfiltrationListItem(
            id=infiltration.id,
            infiltration_date=infiltration.infiltration_date,
            title=infiltration.title,
            content=infiltration.content,
            cafe_name=infiltration.cafe_name,
            url=infiltration.url,
            advertiser_id=infiltration.advertiser_id,
            advertiser_name=(
                infiltration.advertiser.user.company_name
                if infiltration.advertiser and infiltration.advertiser.user
                else None
            ),
            created_at=infiltration.created_at,
        )

    async def delete(self, infiltration_id: int) -> bool:
        """
        카페 침투 삭제 (Admin 전용)

        Args:
            infiltration_id: 침투 ID

        Returns:
            bool: 삭제 성공 여부
        """
        infiltration = await self._repo.get_by_id(infiltration_id)
        if not infiltration:
            return False

        await self._repo.delete(infiltration)
        await self._db.commit()
        return True

    def _build_response(
        self,
        infiltrations: List[CafeInfiltration],
        daily_counts_raw: List[tuple],
    ) -> CafeInfiltrationCalendarResponse:
        """응답 생성"""
        items = []
        for infiltration in infiltrations:
            item = CafeInfiltrationListItem(
                id=infiltration.id,
                infiltration_date=infiltration.infiltration_date,
                title=infiltration.title,
                content=infiltration.content,
                cafe_name=infiltration.cafe_name,
                url=infiltration.url,
                advertiser_id=infiltration.advertiser_id,
                advertiser_name=(
                    infiltration.advertiser.user.company_name
                    if infiltration.advertiser and infiltration.advertiser.user
                    else None
                ),
                created_at=infiltration.created_at,
            )
            items.append(item)

        daily_counts = []
        for infiltration_date, count in daily_counts_raw:
            day_of_week = DAY_OF_WEEK_KO[infiltration_date.weekday()]
            daily_counts.append(
                DailyCount(
                    date=infiltration_date.isoformat(),
                    day_of_week=day_of_week,
                    count=count,
                )
            )

        return CafeInfiltrationCalendarResponse(
            items=items,
            total=len(items),
            daily_counts=daily_counts,
        )
