"""
라우터 패키지

이 패키지는 FastAPI 라우터들을 정의합니다.
"""

from .equipment import router as equipment_router
from .rental import router as rental_router

__all__ = ["equipment_router", "rental_router"]
