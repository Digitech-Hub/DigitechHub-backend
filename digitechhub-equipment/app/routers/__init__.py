"""
라우터 패키지

이 패키지는 FastAPI 라우터들을 정의합니다.
"""

from .admin import router as admin_router
from .equipment import router as equipment_router
from .rental import router as rental_router
from .rental_history import router as rental_history_router

__all__ = ["admin_router", "equipment_router", "rental_router", "rental_history_router"]
