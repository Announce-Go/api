from __future__ import annotations

from app.schemas.tracking.common import (
    RealtimeRankResponse,
    TrackingCreateRequest,
    TrackingCreateResponse,
    TrackingDetailResponse,
    TrackingListResponse,
    TrackingStopResponse,
)

# 블로그 순위 스키마 (공통 스키마 재사용)
# 타입별 특화가 필요한 경우 여기에 추가

BlogRealtimeRankResponse = RealtimeRankResponse
BlogTrackingListResponse = TrackingListResponse
BlogTrackingDetailResponse = TrackingDetailResponse
BlogTrackingCreateRequest = TrackingCreateRequest
BlogTrackingCreateResponse = TrackingCreateResponse
BlogTrackingStopResponse = TrackingStopResponse

__all__ = [
    "BlogRealtimeRankResponse",
    "BlogTrackingListResponse",
    "BlogTrackingDetailResponse",
    "BlogTrackingCreateRequest",
    "BlogTrackingCreateResponse",
    "BlogTrackingStopResponse",
]
