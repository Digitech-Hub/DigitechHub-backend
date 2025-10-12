"""
간단하고 세련된 API 응답 스키마들.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식."""
    
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            # 필요한 경우 커스텀 인코더 추가
        }


class SuccessResponse(BaseModel, Generic[T]):
    """성공 응답 스키마."""
    
    success: bool = True
    message: str
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """에러 응답 스키마."""
    
    success: bool = False
    message: str
    error: Optional[Dict[str, Any]] = None


class ValidationErrorDetail(BaseModel):
    """검증 에러 상세 정보."""
    
    field: str
    message: str
    value: Optional[Any] = None


class ValidationErrorResponse(BaseModel):
    """검증 에러 응답 스키마."""
    
    success: bool = False
    message: str
    error: Optional[Dict[str, Any]] = None


def create_success_response(data: Any = None, message: str = "성공") -> Dict[str, Any]:
    """성공 응답을 생성합니다."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None
    }


def create_error_response(message: str, error: str = None) -> Dict[str, Any]:
    """에러 응답을 생성합니다."""
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": error or message
    }


class RentalHistoryResponse(BaseModel):
    """대여 이력 응답 스키마."""
    
    id: str
    equipment_id: str
    user_id: str
    rental_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    is_returned: bool


class EquipmentStatusInfo(BaseModel):
    """기자재 상태 정보 스키마."""
    
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    is_available: bool
    color_code: Optional[str] = None


class EquipmentInfoResponse(BaseModel):
    """기자재 정보 응답 스키마."""
    
    id: str
    alias: Optional[str] = None
    status: str
    status_display: Optional[str] = None
    status_info: Optional[EquipmentStatusInfo] = None
    type: Optional[str] = None


class RentalResponse(BaseModel):
    """대여 처리 응답 스키마."""
    
    success: bool
    message: str
    rental_history: RentalHistoryResponse
    equipment: EquipmentInfoResponse


class UserRentalInfo(BaseModel):
    """사용자 대여 정보 스키마."""
    
    rental_id: str
    equipment: EquipmentInfoResponse
    rental_date: datetime
    due_date: datetime
    days_remaining: int
    hours_remaining: int
    is_overdue: bool
    time_status: str  # "normal", "expiring_soon", "overdue"


class UserRentalsResponse(BaseModel):
    """사용자 대여 목록 응답 스키마."""
    
    message: str
    rentals: list[UserRentalInfo]
    total_count: int
    overdue_count: int
    expiring_soon_count: int


class RentalDetailInfo(BaseModel):
    """대여 상세 정보 스키마."""
    
    rental_id: str
    equipment: EquipmentInfoResponse
    rental_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    is_returned: bool
    rental_duration: Optional[int] = None  # 대여 기간 (일)
    days_remaining: Optional[int] = None  # 남은 일수 (반납되지 않은 경우)
    hours_remaining: Optional[int] = None  # 남은 시간 (반납되지 않은 경우)
    is_overdue: bool = False
    time_status: str = "normal"  # "normal", "expiring_soon", "overdue", "returned"
    can_extend: bool = False  # 연장 가능 여부


class RentalDetailResponse(BaseModel):
    """대여 상세 응답 스키마."""
    
    message: str
    rental_detail: RentalDetailInfo