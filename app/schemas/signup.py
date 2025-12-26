from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.agency import AgencyCategory


class IdCheckResponse(BaseModel):
    """ID 중복 확인 응답"""

    available: bool
    message: str


class AdvertiserSignupRequest(BaseModel):
    """광고주 회원가입 요청"""

    login_id: str = Field(..., min_length=4, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=100)

    # 파일 ID (업로드 후 전달)
    business_license_file_id: Optional[int] = None
    logo_file_id: Optional[int] = None


class AgencySignupRequest(BaseModel):
    """업체(대행사) 회원가입 요청"""

    login_id: str = Field(..., min_length=4, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=100)

    # 담당 카테고리
    categories: List[AgencyCategory] = Field(default_factory=list)


class SignupResponse(BaseModel):
    """회원가입 응답"""

    success: bool
    message: str
    user_id: Optional[int] = None
