"""
SQLAlchemy 를 사용하기 위한 데이터베이스 설정 모듈
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# MySQL 연결을 위한 URL 형식 (동기식)
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/digitechhub_equipment")
print(SQLALCHEMY_DATABASE_URL)
engine = create_engine(SQLALCHEMY_DATABASE_URL) # 데이터베이스 엔진 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # 세션 생성기

class Base(DeclarativeBase):
    """
    모든 데이터베이스 모델의 기본 클래스
    """
    pass
