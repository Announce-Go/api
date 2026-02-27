from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")


def now_kst() -> datetime:
    """현재 시각 (KST)"""
    return datetime.now(KST)


def now_utc() -> datetime:
    """현재 시각 (UTC)"""
    return datetime.now(UTC)


def today_kst() -> date:
    """오늘 날짜 (KST)"""
    return datetime.now(KST).date()


def _set_timezone(dbapi_conn, connection_record):
    """DB 세션 timezone을 KST로 설정하는 이벤트 핸들러"""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET timezone = 'Asia/Seoul'")
    cursor.close()
