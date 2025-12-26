from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import ApprovalStatus, UserRole


class UserCreate(BaseModel):
    """사용자 생성 요청"""

    login_id: str
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    company_name: Optional[str] = None
    role: UserRole = UserRole.ADVERTISER


class UserResponse(BaseModel):
    """사용자 응답"""

    id: int
    login_id: str
    email: str
    name: str
    phone: Optional[str]
    company_name: Optional[str]
    role: UserRole
    approval_status: ApprovalStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
