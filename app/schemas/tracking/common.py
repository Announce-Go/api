from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.tracking import RankType, TrackingStatus
from app.schemas.pagination import PaginationMeta


# === 실시간 순위 조회 ===


class RealtimeRankResponse(BaseModel):
    """실시간 순위 조회 응답"""

    keyword: str
    url: str
    rank: Optional[int] = Field(None, description="순위 (null=미노출)")
    checked_at: datetime


# === 추적 목록/상세 ===


class TrackingListItem(BaseModel):
    """추적 목록 항목"""

    id: int
    type: RankType
    keyword: str
    url: str
    status: TrackingStatus
    current_session: int

    # 관계 정보
    agency_id: int
    agency_name: Optional[str] = None
    advertiser_id: int
    advertiser_name: Optional[str] = None

    # 최근 순위 (JOIN으로 가져옴)
    latest_rank: Optional[int] = None
    latest_checked_at: Optional[datetime] = None

    created_at: datetime

    model_config = {"from_attributes": True}


class TrackingListResponse(BaseModel):
    """추적 목록 응답"""

    items: List[TrackingListItem]
    total: int
    pagination: PaginationMeta


class RankHistoryItem(BaseModel):
    """순위 히스토리 항목"""

    id: int
    rank: Optional[int] = Field(None, description="순위 (null=미노출)")
    session_number: int = Field(..., description="회차 번호")
    checked_at: datetime

    model_config = {"from_attributes": True}


class TrackingDetailResponse(BaseModel):
    """추적 상세 응답"""

    id: int
    type: RankType
    keyword: str
    url: str
    status: TrackingStatus
    current_session: int

    # 관계 정보
    agency_id: int
    agency_name: Optional[str] = None
    advertiser_id: int
    advertiser_name: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    # 히스토리
    histories: List[RankHistoryItem] = []
    history_total: int = 0


# === 추적 등록 (Agency) ===


class TrackingCreateRequest(BaseModel):
    """추적 등록 요청"""

    keyword: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1)
    advertiser_id: int


class TrackingCreateResponse(BaseModel):
    """추적 등록 응답"""

    id: int
    type: RankType
    keyword: str
    url: str
    status: TrackingStatus
    current_session: int
    advertiser_id: int

    # 초기 순위 정보
    initial_rank: Optional[int] = Field(None, description="등록 시점 순위")
    initial_checked_at: Optional[datetime] = None

    created_at: datetime


# === 추적 중단 (Admin) ===


class TrackingStopResponse(BaseModel):
    """추적 중단 응답"""

    id: int
    status: TrackingStatus
    message: str
