from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class RecentSignupRequest(BaseModel):
    """최근 승인 요청 항목"""

    id: int
    login_id: str
    role: str
    company_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminDashboardResponse(BaseModel):
    """관리자 대시보드 응답 (통합)"""

    # 통계
    pending_signup_count: int  # 승인 대기 수
    advertiser_count: int  # 전체 광고주 수
    agency_count: int  # 전체 업체 수

    # 최근 승인 요청 (5건)
    recent_requests: List[RecentSignupRequest]
