from typing import Optional

from pydantic import BaseModel


class EquipmentStatusInfo(BaseModel):
    """기자재 상태 정보 스키마."""

    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    is_available: bool
    is_active: bool
    color_code: Optional[str] = None