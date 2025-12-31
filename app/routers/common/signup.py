from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_db_session
from app.schemas.signup import (
    AdvertiserSignupRequest,
    AgencySignupRequest,
    IdCheckResponse,
    SignupResponse,
)
from app.services.signup_service import SignupService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/signup", tags=["signup"])


def get_signup_service(
    db: AsyncSession = Depends(get_db_session),
) -> SignupService:
    return SignupService(db)


@router.get("/check-id/{login_id}", response_model=IdCheckResponse)
async def check_id(
    login_id: str,
    service: SignupService = Depends(get_signup_service),
) -> IdCheckResponse:
    """아이디 중복 확인

    Response:
        IdCheckResponse
    """
    available = await service.check_id_available(login_id)
    return IdCheckResponse(
        available=available,
        message="사용 가능한 아이디입니다." if available else "이미 사용 중인 아이디입니다.",
    )


@router.post("/advertiser", response_model=SignupResponse)
async def signup_advertiser(
    request: AdvertiserSignupRequest,
    service: SignupService = Depends(get_signup_service),
) -> SignupResponse:
    """광고주 회원가입

    Request Body:
        AdvertiserSignupRequest

    Response:
        SignupResponse
    """
    try:
        user = await service.register_advertiser(request)
        return SignupResponse(
            success=True,
            message="회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.",
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/agency", response_model=SignupResponse)
async def signup_agency(
    request: AgencySignupRequest,
    service: SignupService = Depends(get_signup_service),
) -> SignupResponse:
    """업체(대행사) 회원가입

    Request Body:
        AgencySignupRequest

    Response:
        SignupResponse
    """
    try:
        user = await service.register_agency(request)
        return SignupResponse(
            success=True,
            message="회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.",
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
