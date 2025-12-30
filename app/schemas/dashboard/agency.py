from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.models.tracking import RankType


class RecentTracking(BaseModel):
    """최근 추적 현황 항목"""

    id: int
    type: RankType
    keyword: str
    latest_rank: Optional[int] = None
    advertiser_name: str

    model_config = {"from_attributes": True}


class AgencyDashboardResponse(BaseModel):
    """업체 대시보드 응답 (통합)"""

    # 통계
    mapped_advertiser_count: int  # 매핑된 광고주 수
    active_tracking_count: int  # 활성 추적 수
    blog_posting_count: int  # 블로그 포스팅 수

    # 최근 추적 현황 (5건)
    recent_tracking: List[RecentTracking]
