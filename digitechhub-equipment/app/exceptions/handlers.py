"""
간단하고 세련된 예외 핸들러들.
"""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.main import app
from app.schemas.output.response import create_error_response
from app.utils.logger import logger


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외를 처리합니다 (404 포함)."""
    detail_str = str(exc.detail) if exc.detail else "알 수 없는 오류"
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(message=detail_str, error=detail_str),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """유효성 검사 에러를 처리합니다."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=422,
        content=create_error_response(
            message="유효성 검사에 실패했습니다", error="; ".join(errors)
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외를 처리합니다."""
    logger.error(f"처리되지 않은 예외: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            message="내부 서버 오류가 발생했습니다",
            error="예상치 못한 오류가 발생했습니다",
        ),
    )
