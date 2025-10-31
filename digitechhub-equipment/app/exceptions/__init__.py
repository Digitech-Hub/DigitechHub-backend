"""
Simple and elegant exception handling package.

이 패키지는 커스텀 예외 클래스와 예외 핸들러를 정의합니다.
"""

from .custom import (BadRequestException, BaseAPIException, ConflictException,
                     ForbiddenException, InternalServerException,
                     NotFoundException, UnauthorizedException,
                     ValidationException)

__all__ = [
    "BaseAPIException",
    "ValidationException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "BadRequestException",
    "InternalServerException"
]