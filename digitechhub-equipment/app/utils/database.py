"""
SQLAlchemy 를 사용하기 위한 데이터베이스 설정 모듈 (비동기 지원)
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# MySQL 연결을 위한 URL 형식 (aiomysql 직접 사용)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/digitechhub_equipment"
)
# 비동기 URL로 변환 (aiomysql 사용)
ASYNC_DATABASE_URL = DATABASE_URL.replace("mysql+pymysql://", "mysql+aiomysql://")
print(f"Async Database URL: {ASYNC_DATABASE_URL}")

# 비동기 엔진 생성 (aiomysql 사용)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # SQL 쿼리 로깅
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300,  # 연결 재사용 시간
    # aiomysql 드라이버 명시적 지정
    connect_args={"charset": "utf8mb4"},
)

# 비동기 세션 생성기
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    모든 데이터베이스 모델의 기본 클래스
    """

    pass
