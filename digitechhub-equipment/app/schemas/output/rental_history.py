from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.output.equipment import EquipmentInfoResponse


class RentalHistoryResponse(BaseModel):
    """대여 이력 응답 스키마."""

    rental_id: str
    equipment_id: str
    user_id: str
    rental_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    is_returned: bool
    is_overdue: bool



class RentalDetailInfo(BaseModel):
    """대여 이력 상세 정보 스키마."""

    rental_id: str
    equipment: EquipmentInfoResponse
    rental_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    is_returned: bool
    rental_duration: Optional[int] = None  # 대여 기간 (일)
    days_remaining: Optional[int] = None  # 남은 일수 (반납되지 않은 경우)
    is_overdue: bool = False
    can_extend: bool = False  # 연장 가능 여부
    extend_count: int = 0  # 연장 횟수

