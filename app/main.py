from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.ranks import router as ranks_router
from app.crawler.browser_pool import BrowserPool
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 수명주기 관리: 브라우저 풀 및 데이터베이스 초기화"""
    # 시작: 데이터베이스 연결 확인
    print("🗄️  데이터베이스 연결 시작...")
    try:
        # 연결 테스트
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ 데이터베이스 연결 성공!")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        raise

    # 브라우저 풀 초기화
    await BrowserPool.get_browser()

    yield

    # 종료: 브라우저 풀 정리
    await BrowserPool.close()
    print("🗄️  데이터베이스 연결 종료")


app = FastAPI(title="Naver Rank Tracker API", version="0.1.0", lifespan=lifespan)

app.include_router(ranks_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/db")
async def db_health_check():
    """데이터베이스 연결 상태 확인"""
    try:
        # 간단한 쿼리 실행
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()
            return {"status": "ok"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"데이터베이스 연결 실패: {str(e)}"
        }
