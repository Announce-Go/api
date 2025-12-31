from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.agency_repository import AgencyRepository
from app.schemas.work_records import CafeInfiltrationCalendarResponse
from app.services.work_records import CafeInfiltrationService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/cafe-infiltration", tags=["agency-cafe-infiltration"])


def get_cafe_infiltration_service(
    db: AsyncSession = Depends(get_db_session),
) -> CafeInfiltrationService:
    return CafeInfiltrationService(db)


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
    response_model=CafeInfiltrationCalendarResponse,
)
async def list_cafe_infiltrations(
    year: int = Query(..., ge=2000, le=2100, description="연도"),
    month: int = Query(..., ge=1, le=12, description="월"),
    agency_id: int = Depends(get_agency_id),
    service: CafeInfiltrationService = Depends(get_cafe_infiltration_service),
) -> CafeInfiltrationCalendarResponse:
    """카페 침투 목록 (매핑된 광고주만 + dailyCounts)

    Response:
        CafeInfiltrationCalendarResponse
    """
    return await service.get_calendar_list_agency(
        agency_id=agency_id,
        year=year,
        month=month,
    )
