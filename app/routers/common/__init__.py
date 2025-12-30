from fastapi import APIRouter

from app.routers.auth import router as auth_router
from .signup import router as signup_router
from .files import router as files_router

# 그룹 라우터 생성
common_router = APIRouter()
common_router.include_router(auth_router)
common_router.include_router(signup_router)
common_router.include_router(files_router)

__all__ = ["common_router"]
