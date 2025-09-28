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
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.utils.logger import logger
from app.utils.database import Base, engine
import app.models

# 환경 변수 로드
load_dotenv()

def init_database():
    """
    데이터베이스 테이블 초기화 함수
    """
    try:
        logger.info("🔧 Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.warning("⚠️ Continuing application startup...")
        return False


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
    init_database()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DigiTech Hub Equipment API...")


def create_app() -> FastAPI:
    """
    FastAPI 애플리케이션 인스턴스 생성 및 설정
    
    Returns:
        FastAPI: 설정된 FastAPI 애플리케이션 인스턴스
    """
    # 데이터베이스 초기화 (create_app 시점에서도 실행)
    init_database()
    
    app = FastAPI(
        title="DigiTech Hub Equipment API",
        description="장비 관리 시스템을 위한 마이크로서비스 API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # CORS 미들웨어 설정
    setup_cors_middleware(app)
    
    # 라우터 등록 (향후 확장용)
    setup_routers(app)
    
    # 미들웨어 설정
    setup_middleware(app)
    
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
    # 향후 라우터 등록
    # app.include_router(equipment_router, prefix="/api/v1/equipment", tags=["equipment"])
    # app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    
    # 기본 헬스체크 엔드포인트
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """
        애플리케이션 상태 확인 엔드포인트
        
        Returns:
            dict: 상태 정보
        """
        return {
            "status": "healthy",
            "message": "DigiTech Hub Equipment API is running",
            "version": "0.1.0"
        }
    
    @app.get("/", tags=["root"])
    async def root() -> dict:
        """
        루트 엔드포인트
        
        Returns:
            dict: API 정보
        """
        return {
            "message": "Welcome to DigiTech Hub Equipment API",
            "docs": "/docs",
            "health": "/health"
        }
    
    logger.info("✅ API routers configured successfully")


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
        start_time = uvicorn.utils.time.time()
        
        # 요청 로깅
        logger.info(f"📥 {request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
        
        response = await call_next(request)
        
        # 응답 로깅
        process_time = uvicorn.utils.time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        
        return response
    
    logger.info("✅ Middleware configured successfully")


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
        port = int(os.getenv("PORT", "8000"))
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


if __name__ == "__main__":
    main()