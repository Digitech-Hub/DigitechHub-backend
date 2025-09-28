"""
간단하고 세련된 커스텀 예외들.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """기본 API 예외 클래스."""
    
    def __init__(
        self,
        message: str = "오류가 발생했습니다",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """유효성 검사 에러 예외."""
    
    def __init__(self, message: str = "유효성 검사에 실패했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 422, details)


class NotFoundException(BaseAPIException):
    """리소스를 찾을 수 없는 예외."""
    
    def __init__(self, message: str = "리소스를 찾을 수 없습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)


class UnauthorizedException(BaseAPIException):
    """인증되지 않은 접근 예외."""
    
    def __init__(self, message: str = "인증되지 않은 접근입니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, details)


class ForbiddenException(BaseAPIException):
    """접근이 금지된 예외."""
    
    def __init__(self, message: str = "접근이 금지되었습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 403, details)


class ConflictException(BaseAPIException):
    """리소스 충돌 예외."""
    
    def __init__(self, message: str = "리소스 충돌이 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 409, details)


class BadRequestException(BaseAPIException):
    """잘못된 요청 예외."""
    
    def __init__(self, message: str = "잘못된 요청입니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)


class InternalServerException(BaseAPIException):
    """내부 서버 에러 예외."""
    
    def __init__(self, message: str = "내부 서버 오류가 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, details)