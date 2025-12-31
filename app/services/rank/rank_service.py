from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.naver import (
    extract_blog_id,
    extract_cafe_id,
    extract_place_id,
    get_blog_rank,
    get_cafe_rank,
    get_place_rank,
)
from app.models.tracking import RankHistory, RankTracking, RankType, TrackingStatus
from app.repositories.tracking import RankHistoryRepository, RankTrackingRepository
from app.schemas.pagination import PaginationMeta
from app.schemas.tracking.common import (
    RankHistoryItem,
    RealtimeRankResponse,
    TrackingCreateRequest,
    TrackingCreateResponse,
    TrackingDetailResponse,
    TrackingListItem,
    TrackingListResponse,
    TrackingStopResponse,
)


class RankService:
    """순위 추적 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._tracking_repo = RankTrackingRepository(db_session)
        self._history_repo = RankHistoryRepository(db_session)

    # === 실시간 순위 조회 ===

    async def get_realtime_rank(
        self,
        rank_type: RankType,
        keyword: str,
        url: str,
    ) -> RealtimeRankResponse:
        """
        실시간 순위 조회 (DB 저장 X)

        Args:
            rank_type: 순위 유형 (place/cafe/blog)
            keyword: 검색 키워드
            url: 추적 대상 URL

        Returns:
            RealtimeRankResponse: 순위 정보
        """
        rank = await self._crawl_rank(rank_type, keyword, url)
        checked_at = datetime.now(timezone.utc)

        return RealtimeRankResponse(
            keyword=keyword,
            url=url,
            rank=rank,
            checked_at=checked_at,
        )

    # === 추적 목록 ===

    async def get_tracking_list(
        self,
        rank_type: RankType,
        status: Optional[TrackingStatus] = None,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TrackingListResponse:
        """
        추적 목록 조회

        Args:
            rank_type: 순위 유형
            status: 상태 필터
            agency_id: 업체 필터 (업체용)
            advertiser_id: 광고주 필터
            keyword: 키워드 검색
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수

        Returns:
            TrackingListResponse: 추적 목록
        """
        skip = (page - 1) * page_size
        trackings = await self._tracking_repo.get_list(
            rank_type=rank_type,
            status=status,
            agency_id=agency_id,
            advertiser_id=advertiser_id,
            keyword=keyword,
            skip=skip,
            limit=page_size,
        )
        total = await self._tracking_repo.count(
            rank_type=rank_type,
            status=status,
            agency_id=agency_id,
            advertiser_id=advertiser_id,
            keyword=keyword,
        )

        # 최신 히스토리 일괄 조회 (N+1 문제 해결)
        tracking_ids = [t.id for t in trackings]
        latest_histories = await self._history_repo.get_latest_by_tracking_ids(
            tracking_ids
        )

        items = []
        for tracking in trackings:
            latest_history = latest_histories.get(tracking.id)

            item = TrackingListItem(
                id=tracking.id,
                type=tracking.type,
                keyword=tracking.keyword,
                url=tracking.url,
                status=tracking.status,
                current_session=tracking.current_session,
                agency_id=tracking.agency_id,
                agency_name=(
                    tracking.agency.user.company_name
                    if tracking.agency and tracking.agency.user
                    else None
                ),
                advertiser_id=tracking.advertiser_id,
                advertiser_name=(
                    tracking.advertiser.user.company_name
                    if tracking.advertiser and tracking.advertiser.user
                    else None
                ),
                latest_rank=latest_history.rank if latest_history else None,
                latest_checked_at=(
                    latest_history.checked_at if latest_history else None
                ),
                created_at=tracking.created_at,
            )
            items.append(item)

        pagination = PaginationMeta.create(total=total, page=page, page_size=page_size)
        return TrackingListResponse(items=items, total=total, pagination=pagination)

    # === 추적 상세 ===

    async def get_tracking_detail(
        self,
        tracking_id: int,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
    ) -> Optional[TrackingDetailResponse]:
        """
        추적 상세 조회

        Args:
            tracking_id: 추적 ID
            agency_id: 업체 ID (업체 접근 시 권한 체크용)
            advertiser_id: 광고주 ID (광고주 접근 시 권한 체크용)

        Returns:
            TrackingDetailResponse: 추적 상세 (없거나 권한 없으면 None)
        """
        tracking = await self._tracking_repo.get_by_id(tracking_id)
        if not tracking:
            return None

        # 권한 체크 (업체/광고주)
        if agency_id and tracking.agency_id != agency_id:
            return None
        if advertiser_id and tracking.advertiser_id != advertiser_id:
            return None

        # 히스토리 전체 가져오기
        histories = await self._history_repo.get_all_by_tracking_id(tracking_id)
        history_total = len(histories)

        return TrackingDetailResponse(
            id=tracking.id,
            type=tracking.type,
            keyword=tracking.keyword,
            url=tracking.url,
            status=tracking.status,
            current_session=tracking.current_session,
            agency_id=tracking.agency_id,
            agency_name=(
                tracking.agency.user.company_name
                if tracking.agency and tracking.agency.user
                else None
            ),
            advertiser_id=tracking.advertiser_id,
            advertiser_name=(
                tracking.advertiser.user.company_name
                if tracking.advertiser and tracking.advertiser.user
                else None
            ),
            created_at=tracking.created_at,
            updated_at=tracking.updated_at,
            histories=[
                RankHistoryItem(
                    id=h.id,
                    rank=h.rank,
                    session_number=h.session_number,
                    checked_at=h.checked_at,
                )
                for h in histories
            ],
            history_total=history_total,
        )

    # === 추적 등록 (Agency) ===

    async def create_tracking(
        self,
        rank_type: RankType,
        data: TrackingCreateRequest,
        agency_id: int,
    ) -> TrackingCreateResponse:
        """
        추적 등록

        - 등록 시 즉시 크롤링하여 1회차 첫 순위 저장

        Args:
            rank_type: 순위 유형
            data: 등록 요청 데이터
            agency_id: 업체 ID

        Returns:
            TrackingCreateResponse: 등록 결과
        """
        # 추적 생성
        tracking = RankTracking(
            type=rank_type,
            agency_id=agency_id,
            advertiser_id=data.advertiser_id,
            keyword=data.keyword,
            url=data.url,
            status=TrackingStatus.ACTIVE,
            current_session=1,
        )
        tracking = await self._tracking_repo.create(tracking)

        # 초기 순위 크롤링
        initial_rank = await self._crawl_rank(rank_type, data.keyword, data.url)
        checked_at = datetime.now(timezone.utc)

        # 1회차 첫 히스토리 저장
        history = RankHistory(
            tracking_id=tracking.id,
            rank=initial_rank,
            session_number=1,
            checked_at=checked_at,
        )
        await self._history_repo.create(history)

        await self._db.commit()

        return TrackingCreateResponse(
            id=tracking.id,
            type=tracking.type,
            keyword=tracking.keyword,
            url=tracking.url,
            status=tracking.status,
            current_session=tracking.current_session,
            advertiser_id=tracking.advertiser_id,
            initial_rank=initial_rank,
            initial_checked_at=checked_at,
            created_at=tracking.created_at,
        )

    # === 추적 중단 (Admin) ===

    async def stop_tracking(self, tracking_id: int) -> Optional[TrackingStopResponse]:
        """
        추적 중단

        Args:
            tracking_id: 추적 ID

        Returns:
            TrackingStopResponse: 중단 결과 (없으면 None)
        """
        tracking = await self._tracking_repo.get_by_id(tracking_id)
        if not tracking:
            return None

        if tracking.status == TrackingStatus.STOPPED:
            return TrackingStopResponse(
                id=tracking.id,
                status=tracking.status,
                message="이미 중단된 추적입니다.",
            )

        tracking.status = TrackingStatus.STOPPED
        await self._tracking_repo.update(tracking)
        await self._db.commit()

        return TrackingStopResponse(
            id=tracking.id,
            status=tracking.status,
            message="추적이 중단되었습니다.",
        )

    # === 내부 헬퍼 메서드 ===

    async def _crawl_rank(
        self,
        rank_type: RankType,
        keyword: str,
        url: str,
    ) -> Optional[int]:
        """
        순위 크롤링

        Args:
            rank_type: 순위 유형
            keyword: 검색 키워드
            url: 추적 대상 URL

        Returns:
            int: 순위 (미노출 시 None)
        """
        if rank_type == RankType.PLACE:
            place_id = extract_place_id(url)
            if not place_id:
                return None
            return await get_place_rank(keyword, place_id)

        elif rank_type == RankType.CAFE:
            cafe_info = extract_cafe_id(url)
            if not cafe_info:
                return None
            cafe_id, article_id = cafe_info
            return await get_cafe_rank(keyword, cafe_id, article_id)

        elif rank_type == RankType.BLOG:
            blog_info = extract_blog_id(url)
            if not blog_info:
                return None
            blog_id, log_no = blog_info
            return await get_blog_rank(keyword, blog_id, log_no)

        return None
