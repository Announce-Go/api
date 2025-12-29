from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.agency_advertiser_mapping_repository import (
    AgencyAdvertiserMappingRepository,
)
from app.repositories.agency_repository import AgencyRepository
from app.schemas.agency import MappedAdvertiserItem, MappedAdvertiserListResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/agency", tags=["agency-common"])


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
    "/advertisers",
    response_model=MappedAdvertiserListResponse,
)
async def list_mapped_advertisers(
    agency_id: int = Depends(get_agency_id),
    db: AsyncSession = Depends(get_db_session),
) -> MappedAdvertiserListResponse:
    """매핑된 광고주 목록 (추적 등록 시 선택용)"""
    mapping_repo = AgencyAdvertiserMappingRepository(db)
    mappings = await mapping_repo.get_by_agency_id(agency_id)

    items = []
    for mapping in mappings:
        if mapping.advertiser and mapping.advertiser.user:
            # Note: advertiser.id = user.id 이므로 user_id 필드 제거됨
            items.append(
                MappedAdvertiserItem(
                    id=mapping.advertiser.id,
                    login_id=mapping.advertiser.user.login_id,
                    name=mapping.advertiser.user.name,
                    company_name=mapping.advertiser.user.company_name,
                )
            )

    return MappedAdvertiserListResponse(items=items, total=len(items))
