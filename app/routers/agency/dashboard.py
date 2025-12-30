from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.agency_repository import AgencyRepository
from app.schemas.dashboard import AgencyDashboardResponse
from app.services.dashboard import AgencyDashboardService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/dashboard", tags=["agency-dashboard"])


def get_dashboard_service(
    db: AsyncSession = Depends(get_db_session),
) -> AgencyDashboardService:
    return AgencyDashboardService(db)


async def get_agency_id(
    current_user: Dict[str, Any] = Depends(require_role("agency")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 업체의 agency_id 반환"""
    agency_repo = AgencyRepository(db)
    agency = await agency_repo.get_by_id(current_user["user_id"])
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="업체 정보를 찾을 수 없습니다.",
        )
    return agency.id


@router.get(
    "",
    response_model=AgencyDashboardResponse,
)
async def get_dashboard(
    agency_id: int = Depends(get_agency_id),
    service: AgencyDashboardService = Depends(get_dashboard_service),
) -> AgencyDashboardResponse:
    """업체 대시보드 (통계 + 최근 추적 현황 5건)"""
    return await service.get_dashboard(agency_id)
