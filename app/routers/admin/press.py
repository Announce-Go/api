from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.schemas.work_records import (
    PressArticleCalendarResponse,
    PressArticleCreateRequest,
    PressArticleListItem,
    PressArticleUpdateRequest,
)
from app.services.work_records import PressArticleService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/press", tags=["admin-press"])


def get_press_article_service(
    db: AsyncSession = Depends(get_db_session),
) -> PressArticleService:
    return PressArticleService(db)


@router.get(
    "",
    response_model=PressArticleCalendarResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_press_articles(
    year: int = Query(..., ge=2000, le=2100, description="연도"),
    month: int = Query(..., ge=1, le=12, description="월"),
    service: PressArticleService = Depends(get_press_article_service),
) -> PressArticleCalendarResponse:
    """언론 기사 목록 (월별 + dailyCounts)"""
    return await service.get_calendar_list_admin(
        year=year,
        month=month,
    )


@router.post(
    "",
    response_model=PressArticleListItem,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
async def create_press_article(
    data: PressArticleCreateRequest,
    service: PressArticleService = Depends(get_press_article_service),
) -> PressArticleListItem:
    """언론 기사 등록"""
    return await service.create(data)


@router.put(
    "/{article_id}",
    response_model=PressArticleListItem,
    dependencies=[Depends(require_role("admin"))],
)
async def update_press_article(
    article_id: int,
    data: PressArticleUpdateRequest,
    service: PressArticleService = Depends(get_press_article_service),
) -> PressArticleListItem:
    """언론 기사 수정"""
    result = await service.update(article_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기사를 찾을 수 없습니다.",
        )
    return result


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
async def delete_press_article(
    article_id: int,
    service: PressArticleService = Depends(get_press_article_service),
) -> None:
    """언론 기사 삭제"""
    success = await service.delete(article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기사를 찾을 수 없습니다.",
        )
