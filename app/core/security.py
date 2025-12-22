from __future__ import annotations

import secrets

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_id() -> str:
    """안전한 세션 ID 생성 (32바이트 URL-safe)"""
    return secrets.token_urlsafe(32)
