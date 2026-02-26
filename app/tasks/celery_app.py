from __future__ import annotations

from celery import Celery, signals
from celery.schedules import crontab

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()


@signals.setup_logging.connect
def on_setup_logging(**kwargs):
    configure_logging()


@signals.after_setup_logger.connect
@signals.after_setup_task_logger.connect
def on_after_setup_logger(logger, **kwargs):
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.propagate = True


def _celery_redis_url() -> str:
    """Celery용 Redis URL (SSL 시 ssl_cert_reqs 파라미터 추가)"""
    url = settings.redis_url
    if settings.REDIS_SSL:
        cert_reqs = "CERT_REQUIRED" if settings.REDIS_SSL_CERT_VERIFY else "CERT_NONE"
        url += f"?ssl_cert_reqs={cert_reqs}"
    return url


def _redbeat_redis_url() -> str:
    """RedBeat용 Redis URL (redis-py 형식의 ssl_cert_reqs 사용)"""
    url = settings.redis_url
    if settings.REDIS_SSL:
        cert_reqs = "required" if settings.REDIS_SSL_CERT_VERIFY else "none"
        url += f"?ssl_cert_reqs={cert_reqs}"
    return url


celery_app = Celery(
    "announce_go",
    broker=_celery_redis_url(),
    backend=_celery_redis_url(),
    include=["app.tasks.rank_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    worker_concurrency=1,
    broker_connection_retry_on_startup=True,
    # 배치 관련 Redis 키 프리픽스
    broker_transport_options={"global_keyprefix": "batch:"},
    result_backend_transport_options={"global_keyprefix": "batch:"},
    # RedBeat: 스케줄 정보를 Redis에 저장
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=_redbeat_redis_url(),
    redbeat_key_prefix="batch:redbeat",
)

celery_app.conf.beat_schedule = {
    "crawl-all-active-trackings": {
        "task": "app.tasks.rank_tasks.crawl_all_active_trackings",
        "schedule": crontab(
            hour=settings.CRAWL_SCHEDULE_HOUR,
            minute=settings.CRAWL_SCHEDULE_MINUTE,
        ),
    },
}
