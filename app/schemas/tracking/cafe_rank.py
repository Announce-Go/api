from __future__ import annotations

from app.schemas.tracking.common import (
    RealtimeRankResponse,
    TrackingCreateRequest,
    TrackingCreateResponse,
    TrackingDetailResponse,
    TrackingListResponse,
    TrackingStopResponse,
)

# 카페 순위 스키마 (공통 스키마 재사용)
# 타입별 특화가 필요한 경우 여기에 추가

CafeRealtimeRankResponse = RealtimeRankResponse
CafeTrackingListResponse = TrackingListResponse
CafeTrackingDetailResponse = TrackingDetailResponse
CafeTrackingCreateRequest = TrackingCreateRequest
CafeTrackingCreateResponse = TrackingCreateResponse
CafeTrackingStopResponse = TrackingStopResponse

__all__ = [
    "CafeRealtimeRankResponse",
    "CafeTrackingListResponse",
    "CafeTrackingDetailResponse",
    "CafeTrackingCreateRequest",
    "CafeTrackingCreateResponse",
    "CafeTrackingStopResponse",
]
