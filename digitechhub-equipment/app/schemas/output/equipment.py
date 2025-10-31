from typing import Optional

from pydantic import BaseModel

from app.schemas.output.equipment_status import EquipmentStatusInfo


class EquipmentInfoResponse(BaseModel):
    """기자재 정보 응답 스키마."""

    id: str
    alias: Optional[str] = None
    status_info: Optional[EquipmentStatusInfo] = None
    type: Optional[str] = None
