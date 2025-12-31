from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.core.dependencies import get_db_session, require_role
from app.schemas.dashboard import AdminDashboardResponse
from app.services.dashboard import AdminDashboardService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/dashboard", tags=["admin-dashboard"])


def get_dashboard_service(
    db: AsyncSession = Depends(get_db_session),
) -> AdminDashboardService:
    return AdminDashboardService(db)


@router.get(
    "",
    response_model=AdminDashboardResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_dashboard(
    service: AdminDashboardService = Depends(get_dashboard_service),
) -> AdminDashboardResponse:
    """관리자 대시보드 (통계 + 최근 승인 요청 5건)

    Response:
        AdminDashboardResponse
    """
    return await service.get_dashboard()
