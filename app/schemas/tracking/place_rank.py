from __future__ import annotations

from app.schemas.tracking.common import (
    RealtimeRankResponse,
    TrackingCreateRequest,
    TrackingCreateResponse,
    TrackingDetailResponse,
    TrackingListResponse,
    TrackingStopResponse,
)

# 플레이스 순위 스키마 (공통 스키마 재사용)
# 타입별 특화가 필요한 경우 여기에 추가

PlaceRealtimeRankResponse = RealtimeRankResponse
PlaceTrackingListResponse = TrackingListResponse
PlaceTrackingDetailResponse = TrackingDetailResponse
PlaceTrackingCreateRequest = TrackingCreateRequest
PlaceTrackingCreateResponse = TrackingCreateResponse
PlaceTrackingStopResponse = TrackingStopResponse

__all__ = [
    "PlaceRealtimeRankResponse",
    "PlaceTrackingListResponse",
    "PlaceTrackingDetailResponse",
    "PlaceTrackingCreateRequest",
    "PlaceTrackingCreateResponse",
    "PlaceTrackingStopResponse",
]
