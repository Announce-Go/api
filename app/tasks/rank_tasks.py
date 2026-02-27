from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import structlog
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.timezone import _set_timezone
from app.crawler.browser_pool import BrowserPool
from app.crawler.naver import (
    extract_blog_id,
    extract_cafe_id,
    extract_place_id,
    get_blog_rank,
    get_cafe_rank,
    get_place_rank,
)
from app.models.tracking import RankHistory, RankTracking, RankType, TrackingStatus
from app.repositories.tracking.rank_history_repository import RankHistoryRepository
from app.repositories.tracking.rank_tracking_repository import RankTrackingRepository
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


def _create_session_factory() -> async_sessionmaker[AsyncSession]:
    """Celery 태스크용 비동기 DB 세션 팩토리 생성"""
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    event.listen(engine.sync_engine, "connect", _set_timezone)
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def _crawl_single_tracking(
    tracking: RankTracking,
    session: AsyncSession,
) -> bool:
    """
    단일 추적 항목 크롤링 및 히스토리 저장

    Returns:
        True: 성공, False: 실패
    """
    history_repo = RankHistoryRepository(session)
    tracking_repo = RankTrackingRepository(session)

    # type별 크롤링
    rank: int | None = None

    if tracking.type == RankType.PLACE:
        place_id = extract_place_id(tracking.url)
        if not place_id:
            logger.error("invalid_url", tracking_id=tracking.id, url=tracking.url)
            return False
        rank = await get_place_rank(tracking.keyword, place_id)

    elif tracking.type == RankType.BLOG:
        blog_info = extract_blog_id(tracking.url)
        if not blog_info:
            logger.error("invalid_url", tracking_id=tracking.id, url=tracking.url)
            return False
        blog_id, log_no = blog_info
        rank = await get_blog_rank(tracking.keyword, blog_id, log_no)

    elif tracking.type == RankType.CAFE:
        cafe_info = extract_cafe_id(tracking.url)
        if not cafe_info:
            logger.error("invalid_url", tracking_id=tracking.id, url=tracking.url)
            return False
        cafe_id, article_id = cafe_info
        rank = await get_cafe_rank(tracking.keyword, cafe_id, article_id)

    # 오늘자 히스토리가 있으면 업데이트, 없으면 생성
    existing_history = await history_repo.get_today_by_tracking_id(
        tracking_id=tracking.id,
        session_number=tracking.current_session,
    )
    if existing_history:
        existing_history.rank = rank
        existing_history.checked_at = datetime.now(timezone.utc)
        await session.flush()
    else:
        history = RankHistory(
            tracking_id=tracking.id,
            rank=rank,
            session_number=tracking.current_session,
            checked_at=datetime.now(timezone.utc),
        )
        await history_repo.create(history)

    # 회차 전환 체크: rank != null인 히스토리가 25개 이상이면 다음 회차
    exposed_count = await history_repo.count_exposures_in_session(
        tracking_id=tracking.id,
        session_number=tracking.current_session,
    )
    if exposed_count >= 25:
        tracking.current_session += 1
        await tracking_repo.update(tracking)
        logger.info(
            "session_advanced",
            tracking_id=tracking.id,
            new_session=tracking.current_session,
        )

    logger.info(
        "tracking_crawled",
        tracking_id=tracking.id,
        keyword=tracking.keyword,
        type=tracking.type.value,
        rank=rank,
        session_number=tracking.current_session,
    )
    return True


async def _crawl_all() -> dict:
    """모든 활성 추적 항목 크롤링 (async 메인 로직)"""
    settings = get_settings()
    session_factory = _create_session_factory()

    total = 0
    success = 0
    fail = 0

    async with session_factory() as session:
        try:
            tracking_repo = RankTrackingRepository(session)

            for rank_type in RankType:
                trackings = await tracking_repo.get_active_trackings_by_type(rank_type)
                logger.info(
                    "batch_type_start",
                    rank_type=rank_type.value,
                    count=len(trackings),
                )

                for tracking in trackings:
                    total += 1
                    try:
                        ok = await _crawl_single_tracking(tracking, session)
                        if ok:
                            success += 1
                        else:
                            fail += 1
                    except Exception:
                        fail += 1
                        logger.error(
                            "tracking_crawl_failed",
                            tracking_id=tracking.id,
                            exc_info=True,
                        )

                    # 크롤링 간 딜레이
                    await asyncio.sleep(settings.CRAWL_DELAY_SECONDS)

            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # 브라우저 풀 정리
            if BrowserPool.is_initialized():
                await BrowserPool.close()

    return {"total": total, "success": success, "fail": fail}


@celery_app.task(name="app.tasks.rank_tasks.crawl_all_active_trackings")
def crawl_all_active_trackings() -> dict:
    """
    모든 활성 추적 항목 크롤링 (Celery 태스크)

    Celery는 동기 환경이므로 asyncio.run()으로 async 코드 실행
    """
    logger.info("batch_start")
    start_time = time.time()

    result = asyncio.run(_crawl_all())

    elapsed = round(time.time() - start_time, 1)
    logger.info(
        "batch_complete",
        total=result["total"],
        success=result["success"],
        fail=result["fail"],
        elapsed_seconds=elapsed,
    )
    return result
