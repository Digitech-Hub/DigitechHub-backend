"""
Simple and elegant exception handling package.

이 패키지는 커스텀 예외 클래스와 예외 핸들러를 정의합니다.
"""

from .handlers import setup_exception_handlers
from .custom import (
    BaseAPIException,
    ValidationException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    BadRequestException,
    InternalServerException
)

__all__ = [
    "setup_exception_handlers",
    "BaseAPIException",
    "ValidationException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "BadRequestException",
    "InternalServerException"
]