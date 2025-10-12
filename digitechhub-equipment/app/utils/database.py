"""
SQLAlchemy 를 사용하기 위한 데이터베이스 설정 모듈 (비동기 지원)
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# MySQL 연결을 위한 비동기 URL 형식
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/digitechhub_equipment")
# 비동기 URL로 변환 (aiomysql 사용)
ASYNC_DATABASE_URL = DATABASE_URL.replace("mysql+pymysql://", "mysql+aiomysql://")
print(f"Async Database URL: {ASYNC_DATABASE_URL}")

# 비동기 엔진 생성
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # SQL 쿼리 로깅
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300,  # 연결 재사용 시간
)

# 비동기 세션 생성기
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """
    모든 데이터베이스 모델의 기본 클래스
    """
    pass

# 동기식 엔진도 유지 (마이그레이션 등을 위해)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sync_engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
