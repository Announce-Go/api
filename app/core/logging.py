from __future__ import annotations

import logging
import sys
from typing import Any, MutableMapping

import structlog
from structlog.types import EventDict

from app.core.config import get_settings
from app.core.timezone import now_kst


_LOG_KEY_ORDER = ("process", "timestamp", "level", "logger", "event")


def _get_process_type() -> str:
    args = " ".join(sys.argv)
    if "celery" in args:
        if "worker" in args:
            return "worker"
        if "beat" in args:
            return "beat"
    return "api"


def _inject_process_type(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    event_dict["process"] = _get_process_type()
    return event_dict


def _add_kst_timestamp(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    event_dict["timestamp"] = now_kst().isoformat()
    return event_dict


def _order_keys(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    ordered = {k: event_dict.pop(k) for k in _LOG_KEY_ORDER if k in event_dict}
    ordered.update(event_dict)
    return ordered  # type: ignore


def _shared_processors() -> list[Any]:
    return [
        structlog.contextvars.merge_contextvars,
        _inject_process_type,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        _add_kst_timestamp,
        structlog.processors.StackInfoRenderer(),
    ]


def configure_logging() -> None:
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.value, logging.INFO)
    shared = _shared_processors()

    structlog.configure(
        processors=shared + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.ExceptionRenderer(),
            _order_keys,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # uvicorn 핸들러 제거 + propagate=True → root JSON 핸들러로 통일
    # (lifespan 이전 메시지는 uvicorn 포맷으로 남음 — 불가피)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(log_level)

    # SQLAlchemy echo=True 가 자체 StreamHandler 를 추가하지 못하도록 NullHandler 선점
    # (엔진 생성 시 "if not logger.handlers" 조건 충족 방지)
    sa_logger = logging.getLogger("sqlalchemy.engine.Engine")
    if not sa_logger.handlers:
        sa_logger.addHandler(logging.NullHandler())
    logging.getLogger("sqlalchemy.engine").setLevel(log_level)
