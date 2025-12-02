from __future__ import annotations

import re
from urllib.parse import quote
from playwright.async_api import async_playwright


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
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(search_url, wait_until="networkidle", timeout=15000)

            # 플레이스 섹션 찾기
            place_section = await page.query_selector('#loc-main-section-root, div[data-hveid="place"], section.sc_new.cs_common_module.case_place, div.place_section')

            if place_section:
                # 플레이스 섹션 내에서 업체명 링크들 찾기
                place_links = await place_section.query_selector_all('a[href*="map.naver.com"][href*="place/"]')
            else:
                # 플레이스 섹션을 못 찾으면 전체에서 검색
                place_links = await page.query_selector_all('a[href*="map.naver.com"][href*="place/"]')

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
