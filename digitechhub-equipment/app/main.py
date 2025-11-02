"""
DigiTech Hub Equipment Microservice API

이 모듈은 장비 관리 시스템의 메인 애플리케이션 진입점을 제공합니다.
FastAPI를 기반으로 하며, CORS 설정과 데이터베이스 초기화를 포함합니다.

Version: 0.1.0
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.abstract_base import Base
from app.routers import admin as admin_router
from app.routers.equipment import router as equipment_router
from app.routers.rental import router as rental_router
from app.routers.rental_history import router as rental_history_router
from app.schemas.input.rental import ExtendRentalRequest, RentEquipmentRequest
from app.schemas.output.equipment import EquipmentInfoResponse
from app.schemas.output.equipment_status import EquipmentStatusInfo
from app.schemas.output.rental import (ExtendRentalResponse, RentalResponse,
                                       ReturnEquipmentResponse)
from app.schemas.output.rental_history import (RentalDetailInfo,
                                               RentalHistoryResponse)
from app.schemas.output.response import (ApiResponse, ErrorResponse,
                                         SuccessResponse,
                                         ValidationErrorDetail,
                                         ValidationErrorResponse,
                                         create_error_response)
from app.utils.database import async_engine
from app.utils.logger import logger
from app.utils.status_initializer import EquipmentStatusInitializer

# 환경 변수 로드
load_dotenv()


async def init_database():
    """
    데이터베이스 테이블 초기화 함수
    """
    try:
        logger.info("🔧 Initializing database tables...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.warning("⚠️ Continuing application startup...")
        return False


def init_statuses():
    """기본 기자재 상태들을 초기화합니다."""
    try:
        print("Initializing default equipment statuses...")

        # 동기식 엔진 생성 (상태 초기화용)
        sync_database_url = os.environ.get(
            "DATABASE_URL",
            "mysql+pymysql://root:password@digitechhub-mysql:3306/digitechhub_equipment",
        )
        sync_engine = create_engine(sync_database_url)
        SyncSessionLocal = sessionmaker(bind=sync_engine)

        with SyncSessionLocal() as sync_session:
            EquipmentStatusInitializer.initialize_default_statuses(sync_session)
            print("Default equipment statuses initialized successfully!")

    except Exception as e:
        print(f"Error during status initialization: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    애플리케이션 생명주기 관리

    시작 시: 데이터베이스 초기화
    종료 시: 리소스 정리
    """
    # Startup
    logger.info("🚀 Starting Digitech Hub Equipment API...")

    # 데이터베이스 초기화
    await init_database()

    yield

    # Shutdown
    logger.info("🛑 Shutting down DigiTech Hub Equipment API...")


def create_app(prefix: str = "/api/equipment") -> FastAPI:
    """
    FastAPI 애플리케이션 인스턴스 생성 및 설정

    Returns:
        FastAPI: 설정된 FastAPI 애플리케이션 인스턴스
    """

    app = FastAPI(
        title="Digitech Hub Equipment API",
        description="장비 관리 시스템을 위한 마이크로서비스 API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        redirect_slashes=True,
        openapi_tags=[
            {
                "name": "Equipment Management",
                "description": "장비 관리 관련 API 엔드포인트",
            },
        ],
    )

    # CORS 미들웨어 설정
    setup_cors_middleware(app)

    # 라우터 등록 (향후 확장용)
    setup_routers(app)

    # 미들웨어 설정
    setup_middleware(app)

    # 스키마 등록
    register_schemas(app)

    # 404 핸들러 직접 등록
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "리소스를 찾을 수 없습니다",
                "data": None,
                "error": "요청한 리소스를 찾을 수 없습니다",
            },
        )

    return app


def setup_cors_middleware(app: FastAPI) -> None:
    """
    CORS 미들웨어 설정

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    origins = [
        "http://localhost:5173",  # Vite 개발 서버
        "http://localhost:8080",  # Vue 개발 서버
        "https://digitech-hub.com",  # 프로덕션 도메인
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    logger.info("✅ CORS middleware configured successfully")


def setup_routers(app: FastAPI) -> None:
    """
    API 라우터 등록

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # 라우터 등록 (더 구체적인 경로부터 등록)
    app.include_router(rental_history_router)
    app.include_router(rental_router)
    app.include_router(admin_router.router)
    app.include_router(equipment_router)


def setup_middleware(app: FastAPI) -> None:
    """
    추가 미들웨어 설정

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        """
        요청 로깅 미들웨어

        Args:
            request: HTTP request object
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response object
        """
        import time

        start_time = time.time()

        # 요청 로깅
        logger.info(
            f"📥 {request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        # 응답 로깅
        process_time = time.time() - start_time
        logger.info(
            f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s"
        )

        return response

    logger.info("✅ Middleware configured successfully")


def register_schemas(app: FastAPI) -> None:
    """
    API 스키마들을 OpenAPI 문서에 등록

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # OpenAPI 스키마에 모델들을 명시적으로 추가
    openapi_schema = app.openapi()

    # 컴포넌트 섹션이 없으면 생성
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}

    # 스키마들을 명시적으로 등록
    schemas_to_register = {
        # 요청 스키마
        "RentEquipmentRequest": RentEquipmentRequest,
        "ExtendRentalRequest": ExtendRentalRequest,
        # 기본 응답 스키마
        "ApiResponse": ApiResponse,
        "SuccessResponse": SuccessResponse,
        "ErrorResponse": ErrorResponse,
        "ValidationErrorDetail": ValidationErrorDetail,
        "ValidationErrorResponse": ValidationErrorResponse,
        # 도메인 응답 스키마
        "RentalHistoryResponse": RentalHistoryResponse,
        "EquipmentStatusInfo": EquipmentStatusInfo,
        "EquipmentInfoResponse": EquipmentInfoResponse,
        "RentalResponse": RentalResponse,
        "RentalDetailInfo": RentalDetailInfo,
        "ExtendRentalResponse": ExtendRentalResponse,
        "ReturnEquipmentResponse": ReturnEquipmentResponse,
    }

    for schema_name, schema_class in schemas_to_register.items():
        try:
            # Pydantic 모델의 JSON 스키마를 가져와서 등록
            openapi_schema["components"]["schemas"][schema_name] = schema_name
            logger.debug(f"✅ Registered schema: {schema_name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to register schema {schema_name}: {e}")

    # OpenAPI 스키마 업데이트
    app.openapi_schema = openapi_schema

    logger.info("✅ Schemas registered successfully in OpenAPI documentation")


def main() -> None:
    """
    애플리케이션 진입점

    개발 환경에서 직접 실행할 때 사용됩니다.
    """
    try:
        logger.info("🎯 Starting DigiTech Hub Equipment API")

        # 애플리케이션 생성
        app = create_app()

        # 서버 설정
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "3001"))
        reload = os.getenv("ENVIRONMENT", "development") == "development"

        logger.info(f"🌐 Server starting: http://{host}:{port}")
        logger.info(f"📚 API documentation: http://{host}:{port}/docs")
        logger.info(f"🔄 Auto reload: {'enabled' if reload else 'disabled'}")

        # 서버 실행
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True,
        )

    except KeyboardInterrupt:
        logger.info("👋 Application terminated by user")
    except Exception as e:
        logger.error(f"💥 Error occurred during application startup: {e}")
        sys.exit(1)


# 서버 인스턴스 생성 (ASGI 서버에서 사용)
app = create_app()


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


if __name__ == "__main__":
    main()
