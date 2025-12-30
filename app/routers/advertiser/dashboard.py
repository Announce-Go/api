from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.advertiser_repository import AdvertiserRepository
from app.schemas.dashboard import AdvertiserDashboardResponse
from app.services.dashboard import AdvertiserDashboardService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/dashboard", tags=["advertiser-dashboard"])


def get_dashboard_service(
    db: AsyncSession = Depends(get_db_session),
) -> AdvertiserDashboardService:
    return AdvertiserDashboardService(db)


async def get_advertiser_id(
    current_user: Dict[str, Any] = Depends(require_role("advertiser")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 광고주의 advertiser_id 반환"""
    advertiser_repo = AdvertiserRepository(db)
    advertiser = await advertiser_repo.get_by_id(current_user["user_id"])
    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고주 정보를 찾을 수 없습니다.",
        )
    return advertiser.id


@router.get(
    "",
    response_model=AdvertiserDashboardResponse,
)
async def get_dashboard(
    advertiser_id: int = Depends(get_advertiser_id),
    service: AdvertiserDashboardService = Depends(get_dashboard_service),
) -> AdvertiserDashboardResponse:
    """광고주 대시보드 (통계 + 최근 추적 현황 5건)"""
    return await service.get_dashboard(advertiser_id)
