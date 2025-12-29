from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MappedAdvertiserItem(BaseModel):
    """업체에 매핑된 광고주 항목 (추적 등록 시 선택용)

    Note: id = user_id 이므로 user_id 필드 제거됨
    """

    id: int  # advertiser.id = user.id
    login_id: str
    name: str
    company_name: Optional[str] = None

    model_config = {"from_attributes": True}


class MappedAdvertiserListResponse(BaseModel):
    """매핑된 광고주 목록 응답"""

    items: List[MappedAdvertiserItem]
    total: int
