"""
간단하고 세련된 API 응답 스키마들.
"""

from typing import Any, Dict, Generic, Optional, TypeVar
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