from __future__ import annotations

import re
import random
from urllib.parse import quote
from playwright.async_api import async_playwright


USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_user_agent() -> str:
    """랜덤 User-Agent 반환"""
    return random.choice(USER_AGENTS)


async def find_place_section(page):
    """
    플레이스 섹션 찾기

    1차: '플레이스' 텍스트가 포함된 헤더의 ancestor 섹션
    2차: 기존 셀렉터로 fallback
    """
    # 1차: 텍스트 기반 탐색
    place_header = await page.query_selector('h2:has-text("플레이스"), strong:has-text("플레이스"), span:has-text("플레이스")')
    if place_header:
        # 헤더의 부모 섹션 찾기 (최대 5단계 상위까지)
        section = await place_header.evaluate_handle('''
            (el) => {
                let current = el;
                for (let i = 0; i < 5; i++) {
                    current = current.parentElement;
                    if (!current) return null;
                    if (current.tagName === 'SECTION' ||
                        current.id?.includes('place') ||
                        current.id?.includes('loc') ||
                        current.className?.includes('place')) {
                        return current;
                    }
                }
                return current;  // 5단계 상위 요소 반환
            }
        ''')
        element = section.as_element()
        if element:
            return element

    # 2차: 기존 셀렉터 fallback
    fallback_selectors = [
        '#loc-main-section-root',
        'div[data-hveid="place"]',
        'section.sc_new.cs_common_module.case_place',
        'div.place_section'
    ]
    for selector in fallback_selectors:
        section = await page.query_selector(selector)
        if section:
            return section

    return None


def extract_place_id(url: str) -> str | None:
    """URL에서 Place ID 추출"""
    patterns = [
        r'/place/(\d+)',
        r'place=(\d+)',
        r'id=(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


async def get_place_rank(keyword: str, place_id: str) -> int | None:
    """
    네이버 검색에서 키워드 검색 후 플레이스 섹션에서 place_id의 순위 반환

    Returns:
        int: 순위 (1부터 시작)
        None: 순위권 외
    """
    search_url = f"https://search.naver.com/search.naver?where=nexearch&query={quote(keyword)}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=get_random_user_agent()
        )
        page = await context.new_page()

        try:
            await page.goto(search_url, wait_until="networkidle", timeout=15000)

            # 플레이스 섹션 찾기
            place_section = await find_place_section(page)

            if not place_section:
                print(f"Error: 플레이스 섹션을 찾을 수 없음 (keyword: {keyword})")
                return None

            # 플레이스 섹션 내에서 업체명 링크들 찾기
            place_links = await place_section.query_selector_all('a[href*="map.naver.com"][href*="place/"]')

            # 중복 제거를 위해 이미 본 place_id 추적
            seen_ids = set()
            rank = 0

            for link in place_links:
                href = await link.get_attribute("href")
                if href:
                    link_place_id = extract_place_id(href)
                    if link_place_id and link_place_id not in seen_ids:
                        seen_ids.add(link_place_id)
                        rank += 1
                        if link_place_id == place_id:
                            return rank

            return None

        except Exception as e:
            print(f"Crawling error: {e}")
            return None

        finally:
            await browser.close()
