from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.work_records.common import DailyCount


class CafeInfiltrationCreateRequest(BaseModel):
    """카페 침투 등록 요청"""

    advertiser_id: int
    infiltration_date: date
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    cafe_name: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = None


class CafeInfiltrationUpdateRequest(BaseModel):
    """카페 침투 수정 요청"""

    infiltration_date: Optional[date] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    cafe_name: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = None


class CafeInfiltrationListItem(BaseModel):
    """카페 침투 목록 항목"""

    id: int
    infiltration_date: date
    title: str
    content: Optional[str] = None
    cafe_name: Optional[str] = None
    url: Optional[str] = None

    # 관계 정보
    advertiser_id: int
    advertiser_name: Optional[str] = None

    created_at: datetime

    model_config = {"from_attributes": True}


class CafeInfiltrationCalendarResponse(BaseModel):
    """카페 침투 캘린더 목록 응답"""

    items: List[CafeInfiltrationListItem]
    total: int
    daily_counts: List[DailyCount]
