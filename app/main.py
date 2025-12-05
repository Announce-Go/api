from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ranks import router as ranks_router
from app.crawler.browser_pool import BrowserPool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 수명주기 관리: 브라우저 풀 초기화 및 정리"""
    # 시작: 브라우저 풀 초기화
    await BrowserPool.get_browser()
    yield
    # 종료: 브라우저 풀 정리
    await BrowserPool.close()


app = FastAPI(title="Naver Rank Tracker API", version="0.1.0", lifespan=lifespan)

app.include_router(ranks_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
