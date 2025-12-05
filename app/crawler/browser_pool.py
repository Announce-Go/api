"""
브라우저 풀 관리 모듈
Playwright 브라우저 인스턴스를 재사용하여 성능 최적화
"""

from __future__ import annotations

import asyncio
from playwright.async_api import async_playwright, Browser, Playwright


class BrowserPool:
    """싱글턴 브라우저 풀"""

    _playwright: Playwright | None = None
    _browser: Browser | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_browser(cls) -> Browser:
        """브라우저 인스턴스 반환 (없으면 생성)"""
        async with cls._lock:
            if cls._browser is None:
                cls._playwright = await async_playwright().start()
                cls._browser = await cls._playwright.chromium.launch(headless=True)
        return cls._browser

    @classmethod
    async def close(cls) -> None:
        """브라우저 풀 정리"""
        async with cls._lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None

    @classmethod
    def is_initialized(cls) -> bool:
        """브라우저 풀 초기화 여부"""
        return cls._browser is not None
