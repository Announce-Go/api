from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.advertiser_repository import AdvertiserRepository
from app.schemas.work_records import PressArticleCalendarResponse
from app.services.work_records import PressArticleService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/advertiser/press", tags=["advertiser-press"])


def get_press_article_service(
    db: AsyncSession = Depends(get_db_session),
) -> PressArticleService:
    return PressArticleService(db)


async def get_advertiser_id(
    current_user: Dict[str, Any] = Depends(require_role("advertiser")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 광고주의 advertiser_id 반환"""
    advertiser_repo = AdvertiserRepository(db)
    advertiser = await advertiser_repo.get_by_id(current_user["user_id"])
    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고주 정보를 찾을 수 없습니다.",
        )
    return advertiser.id


@router.get(
    "",
    response_model=PressArticleCalendarResponse,
)
async def list_press_articles(
    year: int = Query(..., ge=2000, le=2100, description="연도"),
    month: int = Query(..., ge=1, le=12, description="월"),
    advertiser_id: int = Depends(get_advertiser_id),
    service: PressArticleService = Depends(get_press_article_service),
) -> PressArticleCalendarResponse:
    """언론 기사 목록 (본인만 + dailyCounts)"""
    return await service.get_calendar_list_advertiser(
        advertiser_id=advertiser_id,
        year=year,
        month=month,
    )
