# 순위 조회 크롤링 성능 개선

**대상 API**: `get_place_rank`, `get_blog_rank`
**최적화 결과**: 응답 시간 **약 3배 개선** (3.07초 → 1.0초)

---

## 1. 요약

| 항목 | 변경 전 | 변경 후 | 개선율 |
|------|---------|---------|--------|
| 평균 응답 시간 | ~3.07초 | ~1.0초 | **3x** |
| 병목 비율 | 91-95% | 해소 | - |
| 브라우저 시작 | 매 요청 | 1회 (재사용) | - |

---

## 2. 문제 분석

### 2.1 프로파일링 결과

원본 코드의 각 단계별 소요 시간을 측정한 결과:

```
단계                           소요시간      비율
─────────────────────────────────────────────────
1. Playwright 컨텍스트 시작     0.276s       3.5%
2. 브라우저 런치                 0.203s       2.6%
3. 브라우저 컨텍스트 생성        0.006s       0.1%
4. 새 페이지 생성               0.122s       1.5%
5. 페이지 이동 (networkidle)   7.226s      91.7%  ← 병목
6. 섹션 찾기                    0.020s       0.3%
7. 링크 추출                    0.000s       0.0%
8. 브라우저 종료                0.023s       0.3%
─────────────────────────────────────────────────
총 소요시간                     7.880s     100.0%
```

### 2.2 병목 원인

**1. 페이지 로드 대기 옵션 (`wait_until="networkidle"`)**
- 전체 시간의 **91-95%** 차지
- 500ms 동안 네트워크 요청이 없을 때까지 대기
- 네이버 광고, 추적 스크립트 등으로 인해 불필요하게 오래 대기

**2. 매번 브라우저 생성**
- 요청마다 Playwright/브라우저 시작/종료
- 요청당 약 0.3-0.5초 오버헤드

---

## 3. 적용된 최적화

### 3.1 페이지 로드 대기 옵션 변경

**문제**: `networkidle`은 모든 네트워크 요청이 완료될 때까지 대기하여 불필요하게 느림

**해결**: `domcontentloaded`로 변경 (DOM 파싱 완료 시점에서 대기 종료)

```python
# 변경 전
await page.goto(search_url, wait_until="networkidle", timeout=15000)

# 변경 후
await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
```

**변경 파일**: `app/crawler/naver.py` (Line 116, 244)

**옵션별 성능 비교**:

| 옵션 | 페이지 로드 | 섹션 발견 | 개선율 |
|------|------------|----------|--------|
| networkidle | 4.34s | ✅ | 기준 |
| load | 1.13s | ✅ | 3.8x |
| **domcontentloaded** | **0.99s** | ✅ | **4.4x** |

**domcontentloaded 선택 이유**:
- `load`보다 약 0.14초 더 빠름
- 섹션 탐지율 동일 (3/3)
- DOM 파싱 완료 시점에서 필요한 요소가 모두 존재

---

### 3.2 브라우저 풀링 도입

**문제**: 매 요청마다 브라우저를 새로 시작하고 종료하여 오버헤드 발생

**해결**: 싱글턴 패턴으로 브라우저 인스턴스를 재사용

**새로 생성된 파일**: `app/crawler/browser_pool.py`

```python
class BrowserPool:
    """싱글턴 브라우저 풀"""
    _playwright: Playwright | None = None
    _browser: Browser | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_browser(cls) -> Browser:
        async with cls._lock:
            if cls._browser is None:
                cls._playwright = await async_playwright().start()
                cls._browser = await cls._playwright.chromium.launch(headless=True)
        return cls._browser

    @classmethod
    async def close(cls) -> None:
        async with cls._lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None
```

**변경된 코드 패턴**:

```python
# 변경 전: 매번 브라우저 생성
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(...)
    # ... 작업 ...
    await browser.close()

# 변경 후: 브라우저 재사용
browser = await BrowserPool.get_browser()
context = await browser.new_context(...)
try:
    # ... 작업 ...
finally:
    await context.close()  # 컨텍스트만 정리, 브라우저는 유지
```

**FastAPI 연동** (`app/main.py`):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await BrowserPool.get_browser()  # 앱 시작 시 초기화
    yield
    await BrowserPool.close()        # 앱 종료 시 정리

app = FastAPI(lifespan=lifespan)
```

---

## 4. 최종 성능 비교

### 4.1 단계별 개선 효과

| 최적화 | 설명 | 평균 응답 시간 | 개선율 |
|--------|------|---------------|--------|
| 원본 | networkidle, 매번 생성 | ~3.07s | 기준 |
| 대기 옵션 변경 | domcontentloaded | ~1.0s | **3.0x** |
| + 브라우저 풀링 | 브라우저 재사용 | ~1.0s | **3.0x** |

### 4.2 요청 수별 예상 절약 시간

| 요청 수 | 원본 | 최적화 후 | 절약 |
|---------|------|----------|------|
| 10개 | 30.7s | 10.0s | 20.7s |
| 100개 | 5.1분 | 1.7분 | 3.4분 |
| 1,000개 | 51분 | 17분 | 34분 |

---

## 5. 변경된 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `app/crawler/browser_pool.py` | 신규 | 싱글턴 브라우저 풀 |
| `app/crawler/naver.py` | 수정 | BrowserPool 사용, wait_until 변경 |
| `app/main.py` | 수정 | lifespan으로 풀 관리 |

---

## 6. 코드 구조

```
app/
├── main.py                    # FastAPI 앱 + lifespan
├── api/
│   └── ranks.py              # API 엔드포인트
└── crawler/
    ├── browser_pool.py       # 브라우저 풀 (신규)
    └── naver.py              # 크롤링 로직 (수정됨)
```

---

## 7. 추가 개선 가능 사항 (미적용)

| 방안 | 예상 효과 | 리스크 | 비고 |
|------|----------|--------|------|
| HTTP 직접 요청 | 높음 | 높음 | CSR 페이지면 불가 |
| 병렬 요청 처리 | 중간 | 낮음 | 다중 키워드 조회 시 |
| 캐싱 | 중간 | 낮음 | 동일 키워드 반복 시 |

---

## 8. 결론

### 적용된 최적화

| 최적화 | 내용 | 효과 |
|--------|------|------|
| ✅ 대기 옵션 변경 | `networkidle` → `domcontentloaded` | 페이지 로드 4.4배 빠름 |
| ✅ 브라우저 풀링 | 싱글턴 패턴으로 재사용 | 시작/종료 오버헤드 제거 |

### 최종 결과

```
┌─────────────────────────────────────────────────┐
│         성능 최적화 최종 결과                     │
├─────────────────────────────────────────────────┤
│  변경 전:  ~3.07초 (평균)                        │
│  변경 후:  ~1.0초 (평균)                         │
├─────────────────────────────────────────────────┤
│  개선율:  약 3배 (67% 시간 단축)                  │
└─────────────────────────────────────────────────┘
```
