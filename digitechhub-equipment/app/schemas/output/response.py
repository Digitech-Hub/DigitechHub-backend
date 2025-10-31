"""
간단하고 세련된 API 응답 스키마들.
"""

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식."""

    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None


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
    return {"success": True, "message": message, "data": data, "error": None}


def create_error_response(message: str, error: str | None) -> Dict[str, Any]:
    """에러 응답을 생성합니다."""
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": error or message,
    }
