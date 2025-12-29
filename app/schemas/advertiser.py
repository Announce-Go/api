from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class MappedAgencyItem(BaseModel):
    """광고주에 매핑된 업체 항목

    Note: id = user_id 이므로 user_id 필드 제거됨
    """

    id: int  # agency.id = user.id
    login_id: str
    name: str
    company_name: Optional[str] = None

    model_config = {"from_attributes": True}


class MappedAgencyListResponse(BaseModel):
    """매핑된 업체 목록 응답"""

    items: List[MappedAgencyItem]
    total: int
