from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.work_records.common import DailyCount


class PressArticleCreateRequest(BaseModel):
    """언론 기사 등록 요청"""

    advertiser_id: int
    article_date: date
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    url: Optional[str] = None


class PressArticleUpdateRequest(BaseModel):
    """언론 기사 수정 요청"""

    article_date: Optional[date] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    url: Optional[str] = None


class PressArticleListItem(BaseModel):
    """언론 기사 목록 항목"""

    id: int
    article_date: date
    title: str
    content: Optional[str] = None
    url: Optional[str] = None

    # 관계 정보
    advertiser_id: int
    advertiser_name: Optional[str] = None

    created_at: datetime

    model_config = {"from_attributes": True}


class PressArticleCalendarResponse(BaseModel):
    """언론 기사 캘린더 목록 응답"""

    items: List[PressArticleListItem]
    total: int
    daily_counts: List[DailyCount]
