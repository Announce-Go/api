from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field


class DailyCount(BaseModel):
    """날짜별 데이터 개수 (캘린더 UI용)"""

    date: str = Field(..., description="날짜 (YYYY-MM-DD 형식)")
    day_of_week: str = Field(..., description="요일 (월, 화, 수, 목, 금, 토, 일)")
    count: int = Field(..., description="해당 날짜의 데이터 수")


T = TypeVar("T")


class CalendarListResponse(BaseModel, Generic[T]):
    """
    캘린더용 목록 응답 (페이지네이션 없음)

    - items: 해당 월의 전체 데이터 (페이지네이션 없이 한 번에 모두 반환)
    - total: items 개수 (= len(items))
    - daily_counts: 날짜별 데이터 개수 (캘린더에 점/숫자 표시용)
    """

    items: List[T]
    total: int
    daily_counts: List[DailyCount]
