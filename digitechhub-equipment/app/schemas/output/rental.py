from datetime import datetime

from pydantic import BaseModel

from app.schemas.output.equipment import EquipmentInfoResponse


class RentalResponse(BaseModel):
    """대여 처리 응답 스키마."""

    success: bool
    message: str
    equipment: EquipmentInfoResponse


class ExtendRentalResponse(BaseModel):
    """대여 연장 응답 스키마."""

    success: bool
    message: str
    new_due_date: datetime


class ReturnEquipmentResponse(BaseModel):
    """기자재 반환 응답 스키마."""

    success: bool
    message: str
