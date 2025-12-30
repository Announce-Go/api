from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.schemas.dashboard.agency import RecentTracking


class AdvertiserDashboardResponse(BaseModel):
    """광고주 대시보드 응답 (통합)"""

    # 통계
    mapped_agency_count: int  # 매핑된 업체 수
    active_tracking_count: int  # 활성 추적 수
    blog_posting_count: int  # 블로그 포스팅 수

    # 최근 추적 현황 (5건)
    recent_tracking: List[RecentTracking]
