from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.models.tracking import RankType, TrackingStatus
from app.repositories.agency_repository import AgencyRepository
from app.schemas.tracking import (
    RealtimeRankResponse,
    TrackingCreateRequest,
    TrackingCreateResponse,
    TrackingDetailResponse,
    TrackingListResponse,
)
from app.services.rank import RankService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/blog-rank", tags=["agency-blog-rank"])


def get_rank_service(
    db: AsyncSession = Depends(get_db_session),
) -> RankService:
    return RankService(db)


async def get_agency_id(
    current_user: Dict[str, Any] = Depends(require_role("agency")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 업체의 agency_id 반환

    Note: agency.id = user.id 이므로 get_by_id 사용
    """
    agency_repo = AgencyRepository(db)
    agency = await agency_repo.get_by_id(current_user["user_id"])
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="업체 정보를 찾을 수 없습니다.",
        )
    return agency.id


@router.get(
    "/realtime",
    response_model=RealtimeRankResponse,
)
async def get_realtime_rank(
    keyword: str = Query(..., description="검색 키워드"),
    url: str = Query(..., description="블로그 글 URL"),
    agency_id: int = Depends(get_agency_id),
    service: RankService = Depends(get_rank_service),
) -> RealtimeRankResponse:
    """블로그 글 실시간 순위 조회 (DB 저장 X)"""
    return await service.get_realtime_rank(RankType.BLOG, keyword, url)


@router.get(
    "/tracking",
    response_model=TrackingListResponse,
)
async def list_trackings(
    status: Optional[TrackingStatus] = Query(None, description="상태 필터"),
    advertiser_id: Optional[int] = Query(None, description="광고주 필터"),
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agency_id: int = Depends(get_agency_id),
    service: RankService = Depends(get_rank_service),
) -> TrackingListResponse:
    """블로그 글 순위 추적 목록 (본인 업체만)"""
    return await service.get_tracking_list(
        rank_type=RankType.BLOG,
        status=status,
        agency_id=agency_id,
        advertiser_id=advertiser_id,
        keyword=keyword,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/tracking",
    response_model=TrackingCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tracking(
    data: TrackingCreateRequest,
    agency_id: int = Depends(get_agency_id),
    service: RankService = Depends(get_rank_service),
) -> TrackingCreateResponse:
    """블로그 글 순위 추적 등록"""
    return await service.create_tracking(
        rank_type=RankType.BLOG,
        data=data,
        agency_id=agency_id,
    )


@router.get(
    "/tracking/{tracking_id}",
    response_model=TrackingDetailResponse,
)
async def get_tracking_detail(
    tracking_id: int,
    history_skip: int = Query(0, ge=0),
    history_limit: int = Query(100, ge=1, le=1000),
    agency_id: int = Depends(get_agency_id),
    service: RankService = Depends(get_rank_service),
) -> TrackingDetailResponse:
    """블로그 글 순위 추적 상세 (히스토리 포함)"""
    result = await service.get_tracking_detail(
        tracking_id=tracking_id,
        agency_id=agency_id,
        history_skip=history_skip,
        history_limit=history_limit,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추적 정보를 찾을 수 없습니다.",
        )
    return result
