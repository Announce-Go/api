# Naver Rank Tracker API

네이버 검색 결과에서 플레이스/블로그 순위를 조회하는 API

## 설치

### 1. 가상환경 생성 및 활성화

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. Playwright 브라우저 설치

```bash
playwright install chromium
```

## 실행

```bash
uvicorn app.main:app --reload
```

## API 엔드포인트

### 플레이스 순위 조회

```
GET /api/v1/ranks/place?keyword={keyword}&url={url}
```

예시:
```bash
curl "http://localhost:8000/api/v1/ranks/place?keyword=강남%20한의원&url=https://map.naver.com/place/1910250411"
```

### 블로그 순위 조회

```
GET /api/v1/ranks/blog?keyword={keyword}&url={url}
```

예시:
```bash
curl "http://localhost:8000/api/v1/ranks/blog?keyword=강남역%20한의원&url=https://blog.naver.com/dbsaltjd11/224094288224"
```

### 응답

- 순위 (1부터 시작)
- 순위권 외: `-1`

## 테스트

```bash
PYTHONPATH=. python tests/test_naver_rank.py
```
