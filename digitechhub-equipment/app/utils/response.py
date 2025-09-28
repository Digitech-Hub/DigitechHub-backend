"""
API 응답 생성 유틸리티

표준화된 API 응답을 생성하기 위한 헬퍼 함수들입니다.
"""

from typing import Any, Dict, List, Optional, Union

from fastapi import status
from fastapi.responses import JSONResponse

from app.schemas.response import (
    ApiResponse,
    ErrorResponse,
    SuccessResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)


def create_success_response(
    data: Any = None,
    message: str = "요청이 성공적으로 처리되었습니다.",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    성공 응답을 생성합니다.
    
    Args:
        data: 응답 데이터
        message: 응답 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 표준화된 성공 응답
    """
    response_data = SuccessResponse(
        message=message,
        data=data
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )


def create_error_response(
    message: str = "요청 처리 중 오류가 발생했습니다.",
    error_code: str = "INTERNAL_ERROR",
    error_details: Any = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """
    에러 응답을 생성합니다.
    
    Args:
        message: 에러 메시지
        error_code: 에러 코드
        error_details: 에러 상세 정보
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 표준화된 에러 응답
    """
    error_info = {
        "code": error_code,
        "details": error_details
    }
    
    response_data = ErrorResponse(
        message=message,
        error=error_info
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )


def create_validation_error_response(
    validation_errors: List[ValidationErrorDetail],
    message: str = "입력 데이터 검증에 실패했습니다.",
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
) -> JSONResponse:
    """
    검증 에러 응답을 생성합니다.
    
    Args:
        validation_errors: 검증 에러 목록
        message: 에러 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 표준화된 검증 에러 응답
    """
    error_info = {
        "code": "VALIDATION_ERROR",
        "details": [error.model_dump() for error in validation_errors]
    }
    
    response_data = ValidationErrorResponse(
        message=message,
        error=error_info
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )


def create_not_found_response(
    resource: str = "리소스",
    message: Optional[str] = None,
    status_code: int = status.HTTP_404_NOT_FOUND
) -> JSONResponse:
    """
    404 Not Found 응답을 생성합니다.
    
    Args:
        resource: 찾을 수 없는 리소스명
        message: 커스텀 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 404 에러 응답
    """
    if message is None:
        message = f"{resource}을(를) 찾을 수 없습니다."
    
    return create_error_response(
        message=message,
        error_code="NOT_FOUND",
        error_details=f"{resource} not found",
        status_code=status_code
    )


def create_unauthorized_response(
    message: str = "인증이 필요합니다.",
    status_code: int = status.HTTP_401_UNAUTHORIZED
) -> JSONResponse:
    """
    401 Unauthorized 응답을 생성합니다.
    
    Args:
        message: 에러 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 401 에러 응답
    """
    return create_error_response(
        message=message,
        error_code="UNAUTHORIZED",
        error_details="Authentication required",
        status_code=status_code
    )


def create_forbidden_response(
    message: str = "접근 권한이 없습니다.",
    status_code: int = status.HTTP_403_FORBIDDEN
) -> JSONResponse:
    """
    403 Forbidden 응답을 생성합니다.
    
    Args:
        message: 에러 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 403 에러 응답
    """
    return create_error_response(
        message=message,
        error_code="FORBIDDEN",
        error_details="Access denied",
        status_code=status_code
    )


def create_bad_request_response(
    message: str = "잘못된 요청입니다.",
    error_details: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    400 Bad Request 응답을 생성합니다.
    
    Args:
        message: 에러 메시지
        error_details: 에러 상세 정보
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 400 에러 응답
    """
    return create_error_response(
        message=message,
        error_code="BAD_REQUEST",
        error_details=error_details,
        status_code=status_code
    )


def create_conflict_response(
    message: str = "요청이 현재 리소스 상태와 충돌합니다.",
    error_details: Any = None,
    status_code: int = status.HTTP_409_CONFLICT
) -> JSONResponse:
    """
    409 Conflict 응답을 생성합니다.
    
    Args:
        message: 에러 메시지
        error_details: 에러 상세 정보
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse: 409 에러 응답
    """
    return create_error_response(
        message=message,
        error_code="CONFLICT",
        error_details=error_details,
        status_code=status_code
    )


# 편의 함수들
def success(data: Any = None, message: str = "요청이 성공적으로 처리되었습니다.") -> JSONResponse:
    """성공 응답 생성 편의 함수"""
    return create_success_response(data=data, message=message)


def error(message: str = "요청 처리 중 오류가 발생했습니다.", status_code: int = 500) -> JSONResponse:
    """에러 응답 생성 편의 함수"""
    return create_error_response(message=message, status_code=status_code)


def not_found(resource: str = "리소스") -> JSONResponse:
    """404 응답 생성 편의 함수"""
    return create_not_found_response(resource=resource)


def unauthorized(message: str = "인증이 필요합니다.") -> JSONResponse:
    """401 응답 생성 편의 함수"""
    return create_unauthorized_response(message=message)


def forbidden(message: str = "접근 권한이 없습니다.") -> JSONResponse:
    """403 응답 생성 편의 함수"""
    return create_forbidden_response(message=message)


def bad_request(message: str = "잘못된 요청입니다.") -> JSONResponse:
    """400 응답 생성 편의 함수"""
    return create_bad_request_response(message=message)
