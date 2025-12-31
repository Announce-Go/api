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


router = APIRouter(prefix="/blog-rank", tags=["admin-blog-rank"])


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
    url: str = Query(..., description="블로그 글 URL"),
    service: RankService = Depends(get_rank_service),
) -> RealtimeRankResponse:
    """블로그 글 실시간 순위 조회 (DB 저장 X)"""
    return await service.get_realtime_rank(RankType.BLOG, keyword, url)


@router.get(
    "/tracking",
    response_model=TrackingListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_trackings(
    status: Optional[TrackingStatus] = Query(None, description="상태 필터"),
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=1000, description="페이지당 항목 수"),
    service: RankService = Depends(get_rank_service),
) -> TrackingListResponse:
    """블로그 글 순위 추적 목록 (전체)"""
    return await service.get_tracking_list(
        rank_type=RankType.BLOG,
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/tracking/{tracking_id}",
    response_model=TrackingDetailResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_tracking_detail(
    tracking_id: int,
    service: RankService = Depends(get_rank_service),
) -> TrackingDetailResponse:
    """블로그 글 순위 추적 상세 (히스토리 전체 포함)"""
    result = await service.get_tracking_detail(
        tracking_id=tracking_id,
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
    """블로그 글 순위 추적 중단"""
    result = await service.stop_tracking(tracking_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추적 정보를 찾을 수 없습니다.",
        )
    return result
