from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.agency import AgencyCategory
from app.models.user import ApprovalStatus, UserRole
from app.schemas.file import FileResponse


# === 회원가입 승인 요청 ===


class SignupRequestItem(BaseModel):
    """회원가입 승인 요청 목록 항목"""

    id: int
    login_id: str
    email: str
    name: str
    phone: Optional[str]
    company_name: Optional[str]
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class SignupRequestListResponse(BaseModel):
    """회원가입 승인 요청 목록 응답"""

    items: List[SignupRequestItem]
    total: int


class SignupRequestDetailResponse(BaseModel):
    """회원가입 승인 요청 상세 응답"""

    id: int
    login_id: str
    email: str
    name: str
    phone: Optional[str]
    company_name: Optional[str]
    role: UserRole
    created_at: datetime

    # 광고주인 경우 파일 정보
    business_license_file: Optional[FileResponse] = None
    logo_file: Optional[FileResponse] = None

    # 업체인 경우 카테고리
    categories: Optional[List[AgencyCategory]] = None


class ApproveRequest(BaseModel):
    """승인 요청 (업체인 경우 광고주 매핑 포함)"""

    advertiser_ids: Optional[List[int]] = None


class RejectRequest(BaseModel):
    """거절 요청"""

    pass  # 거절 사유 없음


class ApprovalResponse(BaseModel):
    """승인/거절 응답"""

    success: bool
    message: str


# === 광고주 관리 ===


class AdvertiserListItem(BaseModel):
    """광고주 목록 항목"""

    id: int
    user_id: int
    login_id: str
    email: str
    name: str
    company_name: Optional[str]
    approval_status: ApprovalStatus
    business_license_file: Optional[FileResponse] = None
    logo_file: Optional[FileResponse] = None
    created_at: datetime


class AdvertiserListResponse(BaseModel):
    """광고주 목록 응답"""

    items: List[AdvertiserListItem]
    total: int


class MappedAgencyItem(BaseModel):
    """매핑된 업체 정보"""

    id: int
    agency_id: int
    agency_name: str
    agency_company_name: Optional[str]


class AdvertiserDetailResponse(BaseModel):
    """광고주 상세 응답"""

    id: int
    user_id: int
    login_id: str
    email: str
    name: str
    phone: Optional[str]
    company_name: Optional[str]
    approval_status: ApprovalStatus
    business_license_file: Optional[FileResponse] = None
    logo_file: Optional[FileResponse] = None
    created_at: datetime

    # 매핑된 업체 목록
    mapped_agencies: List[MappedAgencyItem]


# === 업체 관리 ===


class AgencyListItem(BaseModel):
    """업체 목록 항목"""

    id: int
    user_id: int
    login_id: str
    email: str
    name: str
    company_name: Optional[str]
    categories: List[AgencyCategory]
    approval_status: ApprovalStatus
    created_at: datetime


class AgencyListResponse(BaseModel):
    """업체 목록 응답"""

    items: List[AgencyListItem]
    total: int


class MappedAdvertiserItem(BaseModel):
    """매핑된 광고주 정보"""

    id: int
    advertiser_id: int
    advertiser_name: str
    advertiser_company_name: Optional[str]


class AgencyDetailResponse(BaseModel):
    """업체 상세 응답"""

    id: int
    user_id: int
    login_id: str
    email: str
    name: str
    phone: Optional[str]
    company_name: Optional[str]
    categories: List[AgencyCategory]
    approval_status: ApprovalStatus
    created_at: datetime

    # 매핑된 광고주 목록
    mapped_advertisers: List[MappedAdvertiserItem]
