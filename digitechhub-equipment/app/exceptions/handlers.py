"""
간단하고 세련된 예외 핸들러들.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.schemas.response import create_success_response, create_error_response
from app.utils.logger import logger


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외를 처리합니다 (404 포함)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.detail,
            error=exc.detail
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """유효성 검사 에러를 처리합니다."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            message="유효성 검사에 실패했습니다",
            error="; ".join(errors)
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외를 처리합니다."""
    logger.error(f"처리되지 않은 예외: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            message="내부 서버 오류가 발생했습니다",
            error="예상치 못한 오류가 발생했습니다"
        )
    )


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러를 설정합니다."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ Successfully setup to exception handlers")