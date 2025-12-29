from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.models.tracking import RankType, TrackingStatus
from app.schemas.tracking import (
    RealtimeRankResponse,
    TrackingDetailResponse,
    TrackingListResponse,
    TrackingStopResponse,
)
from app.services.rank import RankService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/admin/place-rank", tags=["admin-place-rank"])


def get_rank_service(
    db: AsyncSession = Depends(get_db_session),
) -> RankService:
    return RankService(db)


@router.get(
    "/realtime",
    response_model=RealtimeRankResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_realtime_rank(
    keyword: str = Query(..., description="검색 키워드"),
    url: str = Query(..., description="플레이스 URL"),
    service: RankService = Depends(get_rank_service),
) -> RealtimeRankResponse:
    """플레이스 실시간 순위 조회 (DB 저장 X)"""
    return await service.get_realtime_rank(RankType.PLACE, keyword, url)


@router.get(
    "/tracking",
    response_model=TrackingListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_trackings(
    status: Optional[TrackingStatus] = Query(None, description="상태 필터"),
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RankService = Depends(get_rank_service),
) -> TrackingListResponse:
    """플레이스 순위 추적 목록 (전체)"""
    return await service.get_tracking_list(
        rank_type=RankType.PLACE,
        status=status,
        keyword=keyword,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/tracking/{tracking_id}",
    response_model=TrackingDetailResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_tracking_detail(
    tracking_id: int,
    history_skip: int = Query(0, ge=0),
    history_limit: int = Query(100, ge=1, le=1000),
    service: RankService = Depends(get_rank_service),
) -> TrackingDetailResponse:
    """플레이스 순위 추적 상세 (히스토리 포함)"""
    result = await service.get_tracking_detail(
        tracking_id=tracking_id,
        history_skip=history_skip,
        history_limit=history_limit,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추적 정보를 찾을 수 없습니다.",
        )
    return result


@router.put(
    "/tracking/{tracking_id}/stop",
    response_model=TrackingStopResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def stop_tracking(
    tracking_id: int,
    service: RankService = Depends(get_rank_service),
) -> TrackingStopResponse:
    """플레이스 순위 추적 중단"""
    result = await service.stop_tracking(tracking_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추적 정보를 찾을 수 없습니다.",
        )
    return result
