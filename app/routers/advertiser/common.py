from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.advertiser_repository import AdvertiserRepository
from app.repositories.agency_advertiser_mapping_repository import (
    AgencyAdvertiserMappingRepository,
)
from app.schemas.advertiser import MappedAgencyItem, MappedAgencyListResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="", tags=["advertiser-common"])


async def get_advertiser_id(
    current_user: Dict[str, Any] = Depends(require_role("advertiser")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 광고주의 advertiser_id 반환

    Note: advertiser.id = user.id 이므로 get_by_id 사용
    """
    advertiser_repo = AdvertiserRepository(db)
    advertiser = await advertiser_repo.get_by_id(current_user["user_id"])
    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고주 정보를 찾을 수 없습니다.",
        )
    return advertiser.id


@router.get(
    "/agencies",
    response_model=MappedAgencyListResponse,
)
async def list_mapped_agencies(
    advertiser_id: int = Depends(get_advertiser_id),
    db: AsyncSession = Depends(get_db_session),
) -> MappedAgencyListResponse:
    """매핑된 업체 목록

    Response:
        MappedAgencyListResponse
    """
    mapping_repo = AgencyAdvertiserMappingRepository(db)
    mappings = await mapping_repo.get_by_advertiser_id(advertiser_id)

    items = []
    for mapping in mappings:
        if mapping.agency and mapping.agency.user:
            items.append(
                MappedAgencyItem(
                    id=mapping.agency.id,
                    login_id=mapping.agency.user.login_id,
                    name=mapping.agency.user.name,
                    company_name=mapping.agency.user.company_name,
                )
            )

    return MappedAgencyListResponse(items=items, total=len(items))
