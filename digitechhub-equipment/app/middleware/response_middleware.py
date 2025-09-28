"""
API 응답을 표준화하기 위한 간단하고 세련된 응답 미들웨어.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.utils.logger import logger


class ResponseMiddleware:
    """간단한 응답 표준화 미들웨어."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 요청 객체 생성
        request = Request(scope, receive)
        request.state.request_id = request_id
        
        # 응답 처리
        response = await self.app(scope, receive, send)
        
        # 현재는 단순히 통과 - 예외 핸들러에서 변환 처리
        return response


def setup_response_middleware(app):
    """응답 미들웨어를 설정합니다."""
    app.add_middleware(ResponseMiddleware)
    logger.info("✅ 간단한 응답 미들웨어가 성공적으로 설정되었습니다")