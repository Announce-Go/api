from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.models.user import ApprovalStatus, UserRole
from app.schemas.admin import (
    AdvertiserDetailResponse,
    AdvertiserListItem,
    AdvertiserListResponse,
    AgencyDetailResponse,
    AgencyListItem,
    AgencyListResponse,
    ApprovalResponse,
    ApproveRequest,
    MappedAdvertiserItem,
    MappedAgencyItem,
    RejectRequest,
    SignupRequestDetailResponse,
    SignupRequestItem,
    SignupRequestListResponse,
)
from app.schemas.file import FileResponse
from app.services.admin_member_service import AdminMemberService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service(
    db: AsyncSession = Depends(get_db_session),
) -> AdminMemberService:
    return AdminMemberService(db)


# === 회원가입 승인 요청 ===


@router.get(
    "/signup-requests",
    response_model=SignupRequestListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_signup_requests(
    role: Optional[UserRole] = Query(None, description="역할 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AdminMemberService = Depends(get_admin_service),
) -> SignupRequestListResponse:
    """회원가입 승인 요청 목록 (필터, 검색)"""
    users, total = await service.get_pending_signups(role, skip, limit)
    return SignupRequestListResponse(
        items=[SignupRequestItem.model_validate(u) for u in users],
        total=total,
    )


@router.get(
    "/signup-requests/{user_id}",
    response_model=SignupRequestDetailResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_signup_request_detail(
    user_id: int,
    service: AdminMemberService = Depends(get_admin_service),
) -> SignupRequestDetailResponse:
    """회원가입 승인 요청 상세"""
    user = await service.get_signup_request_detail(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="요청을 찾을 수 없습니다.",
        )

    response = SignupRequestDetailResponse(
        id=user.id,
        login_id=user.login_id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        company_name=user.company_name,
        role=user.role,
        created_at=user.created_at,
    )

    # 광고주인 경우 파일 정보 추가
    if user.role == UserRole.ADVERTISER and user.advertiser:
        if user.advertiser.business_license_file:
            response.business_license_file = FileResponse.model_validate(
                user.advertiser.business_license_file
            )
        if user.advertiser.logo_file:
            response.logo_file = FileResponse.model_validate(user.advertiser.logo_file)

    # 업체인 경우 카테고리 추가
    if user.role == UserRole.AGENCY and user.agency:
        response.categories = user.agency.categories

    return response


@router.post(
    "/signup-requests/{user_id}/approve",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def approve_signup(
    user_id: int,
    request: ApproveRequest,
    service: AdminMemberService = Depends(get_admin_service),
) -> ApprovalResponse:
    """회원가입 승인 (업체인 경우 광고주 매핑 포함)"""
    try:
        await service.approve_signup(user_id, request.advertiser_ids)
        return ApprovalResponse(success=True, message="승인되었습니다.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/signup-requests/{user_id}/reject",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def reject_signup(
    user_id: int,
    request: RejectRequest,
    service: AdminMemberService = Depends(get_admin_service),
) -> ApprovalResponse:
    """회원가입 거절"""
    try:
        await service.reject_signup(user_id)
        return ApprovalResponse(success=True, message="거절되었습니다.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# === 광고주 관리 ===


@router.get(
    "/advertisers",
    response_model=AdvertiserListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_advertisers(
    approval_status: Optional[ApprovalStatus] = Query(None),
    search: Optional[str] = Query(None, description="이름/회사명/이메일 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AdminMemberService = Depends(get_admin_service),
) -> AdvertiserListResponse:
    """광고주 목록 (검색)"""
    advertisers, total = await service.get_advertisers(
        approval_status, search, skip, limit
    )

    items = []
    for adv in advertisers:
        item = AdvertiserListItem(
            id=adv.id,
            user_id=adv.user_id,
            login_id=adv.user.login_id,
            email=adv.user.email,
            name=adv.user.name,
            company_name=adv.user.company_name,
            approval_status=adv.user.approval_status,
            business_license_file=(
                FileResponse.model_validate(adv.business_license_file)
                if adv.business_license_file
                else None
            ),
            logo_file=(
                FileResponse.model_validate(adv.logo_file) if adv.logo_file else None
            ),
            created_at=adv.user.created_at,
        )
        items.append(item)

    return AdvertiserListResponse(items=items, total=total)


@router.get(
    "/advertisers/{advertiser_id}",
    response_model=AdvertiserDetailResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_advertiser_detail(
    advertiser_id: int,
    service: AdminMemberService = Depends(get_admin_service),
) -> AdvertiserDetailResponse:
    """광고주 상세 및 매핑된 업체 목록"""
    advertiser, mappings = await service.get_advertiser_detail(advertiser_id)

    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고주를 찾을 수 없습니다.",
        )

    mapped_agencies = []
    for mapping in mappings:
        if mapping.agency and mapping.agency.user:
            mapped_agencies.append(
                MappedAgencyItem(
                    id=mapping.id,
                    agency_id=mapping.agency_id,
                    agency_name=mapping.agency.user.name,
                    agency_company_name=mapping.agency.user.company_name,
                )
            )

    return AdvertiserDetailResponse(
        id=advertiser.id,
        user_id=advertiser.user_id,
        login_id=advertiser.user.login_id,
        email=advertiser.user.email,
        name=advertiser.user.name,
        phone=advertiser.user.phone,
        company_name=advertiser.user.company_name,
        approval_status=advertiser.user.approval_status,
        business_license_file=(
            FileResponse.model_validate(advertiser.business_license_file)
            if advertiser.business_license_file
            else None
        ),
        logo_file=(
            FileResponse.model_validate(advertiser.logo_file)
            if advertiser.logo_file
            else None
        ),
        created_at=advertiser.user.created_at,
        mapped_agencies=mapped_agencies,
    )


# === 업체 관리 ===


@router.get(
    "/agencies",
    response_model=AgencyListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_agencies(
    approval_status: Optional[ApprovalStatus] = Query(None),
    search: Optional[str] = Query(None, description="이름/회사명/이메일 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AdminMemberService = Depends(get_admin_service),
) -> AgencyListResponse:
    """업체 목록 (검색)"""
    agencies, total = await service.get_agencies(
        approval_status, search, skip, limit
    )

    items = []
    for agency in agencies:
        item = AgencyListItem(
            id=agency.id,
            user_id=agency.user_id,
            login_id=agency.user.login_id,
            email=agency.user.email,
            name=agency.user.name,
            company_name=agency.user.company_name,
            categories=agency.categories or [],
            approval_status=agency.user.approval_status,
            created_at=agency.user.created_at,
        )
        items.append(item)

    return AgencyListResponse(items=items, total=total)


@router.get(
    "/agencies/{agency_id}",
    response_model=AgencyDetailResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_agency_detail(
    agency_id: int,
    service: AdminMemberService = Depends(get_admin_service),
) -> AgencyDetailResponse:
    """업체 상세 및 매핑된 광고주 목록"""
    agency, mappings = await service.get_agency_detail(agency_id)

    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="업체를 찾을 수 없습니다.",
        )

    mapped_advertisers = []
    for mapping in mappings:
        if mapping.advertiser and mapping.advertiser.user:
            mapped_advertisers.append(
                MappedAdvertiserItem(
                    id=mapping.id,
                    advertiser_id=mapping.advertiser_id,
                    advertiser_name=mapping.advertiser.user.name,
                    advertiser_company_name=mapping.advertiser.user.company_name,
                )
            )

    return AgencyDetailResponse(
        id=agency.id,
        user_id=agency.user_id,
        login_id=agency.user.login_id,
        email=agency.user.email,
        name=agency.user.name,
        phone=agency.user.phone,
        company_name=agency.user.company_name,
        categories=agency.categories or [],
        approval_status=agency.user.approval_status,
        created_at=agency.user.created_at,
        mapped_advertisers=mapped_advertisers,
    )
