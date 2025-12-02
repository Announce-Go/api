from fastapi import FastAPI

from app.api.ranks import router as ranks_router

app = FastAPI(title="Naver Rank Tracker API", version="0.1.0")

app.include_router(ranks_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
