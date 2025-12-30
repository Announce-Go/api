from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.schemas.work_records import (
    CafeInfiltrationCalendarResponse,
    CafeInfiltrationCreateRequest,
    CafeInfiltrationListItem,
    CafeInfiltrationUpdateRequest,
)
from app.services.work_records import CafeInfiltrationService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/cafe-infiltration", tags=["admin-cafe-infiltration"])


def get_cafe_infiltration_service(
    db: AsyncSession = Depends(get_db_session),
) -> CafeInfiltrationService:
    return CafeInfiltrationService(db)


@router.get(
    "",
    response_model=CafeInfiltrationCalendarResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_cafe_infiltrations(
    year: int = Query(..., ge=2000, le=2100, description="연도"),
    month: int = Query(..., ge=1, le=12, description="월"),
    service: CafeInfiltrationService = Depends(get_cafe_infiltration_service),
) -> CafeInfiltrationCalendarResponse:
    """카페 침투 목록 (월별 + dailyCounts)"""
    return await service.get_calendar_list_admin(
        year=year,
        month=month,
    )


@router.post(
    "",
    response_model=CafeInfiltrationListItem,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
async def create_cafe_infiltration(
    data: CafeInfiltrationCreateRequest,
    service: CafeInfiltrationService = Depends(get_cafe_infiltration_service),
) -> CafeInfiltrationListItem:
    """카페 침투 등록"""
    return await service.create(data)


@router.put(
    "/{infiltration_id}",
    response_model=CafeInfiltrationListItem,
    dependencies=[Depends(require_role("admin"))],
)
async def update_cafe_infiltration(
    infiltration_id: int,
    data: CafeInfiltrationUpdateRequest,
    service: CafeInfiltrationService = Depends(get_cafe_infiltration_service),
) -> CafeInfiltrationListItem:
    """카페 침투 수정"""
    result = await service.update(infiltration_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="침투 기록을 찾을 수 없습니다.",
        )
    return result


@router.delete(
    "/{infiltration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
async def delete_cafe_infiltration(
    infiltration_id: int,
    service: CafeInfiltrationService = Depends(get_cafe_infiltration_service),
) -> None:
    """카페 침투 삭제"""
    success = await service.delete(infiltration_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="침투 기록을 찾을 수 없습니다.",
        )
