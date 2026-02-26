from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.models.user import ApprovalStatus, UserRole


class LoginRequest(BaseModel):
    """로그인 요청"""

    login_id: str
    password: str
    remember_me: bool = False


class UserInfo(BaseModel):
    """사용자 정보 (세션/응답용)"""

    id: int
    login_id: str
    email: str
    name: str
    role: UserRole
    approval_status: ApprovalStatus
    categories: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """로그인 응답"""

    user: UserInfo


class SessionResponse(BaseModel):
    """세션 확인 응답"""

    authenticated: bool
    user: Optional[UserInfo] = None


class LogoutResponse(BaseModel):
    """로그아웃 응답"""

    success: bool
    message: str
