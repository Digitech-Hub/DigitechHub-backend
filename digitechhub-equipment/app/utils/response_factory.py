"""
간단하고 세련된 응답 팩토리.
"""

from typing import Any

from fastapi.responses import JSONResponse

from app.schemas.output.response import (create_error_response,
                                         create_success_response)


class ResponseFactory:
    """간단한 응답 팩토리 클래스."""

    @staticmethod
    def success(data: Any = None, message: str = "성공") -> JSONResponse:
        """성공 응답을 생성합니다."""
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        return JSONResponse(
            status_code=200, content=create_success_response(data, message)
        )

    @staticmethod
    def error(
        message: str, status_code: int = 400, error: str | None = None
    ) -> JSONResponse:
        """에러 응답을 생성합니다."""
        return JSONResponse(
            status_code=status_code, content=create_error_response(message, error)
        )

    @staticmethod
    def fail(
        message: str,
        error: str,
        status_code: int = 200,
    ) -> JSONResponse:
        """HTTP 200으로 논리적 실패 형태의 응답을 생성합니다.

        예시 페이로드 형태:
        {"success": false, "message": "...", "error": "..."}
        """
        return JSONResponse(
            status_code=status_code, content=create_error_response(message, error)
        )

    @staticmethod
    def error_detail(
        message: str,
        error: Any,
        status_code: int = 400,
    ) -> JSONResponse:
        """에러 상세 객체를 포함한 응답을 생성합니다.

        예시 페이로드 형태:
        {
          "success": false,
          "message": "Failed to retrieve today's timetable",
          "data": null,
          "error": {
            "code": "INFO-200",
            "reason": "NEIS API error",
            "detail": "해당하는 데이터가 없습니다."
          }
        }
        """
        return JSONResponse(
            status_code=status_code, content=create_error_response(message, error)
        )

    @staticmethod
    def not_found(message: str = "리소스를 찾을 수 없습니다") -> JSONResponse:
        """404 응답을 생성합니다."""
        return ResponseFactory.error(message, 404)

    @staticmethod
    def bad_request(message: str = "잘못된 요청입니다") -> JSONResponse:
        """400 응답을 생성합니다."""
        return ResponseFactory.error(message, 400)

    @staticmethod
    def internal_error(message: str = "내부 서버 오류가 발생했습니다") -> JSONResponse:
        """500 응답을 생성합니다."""
        return ResponseFactory.error(message, 500)
