"""
프로젝트 전역에서 사용하는 의존성 주입 유틸리티를 정의합니다.
"""
from sqlalchemy.orm import Session
from typing import Generator
from .database import SessionLocal
from .logger import logger

def get_database() -> Generator[Session, None, None]:
    """
    데이터베이스 세션을 생성하고 반환하는 제너레이터 함수입니다.
    사용 후 세션을 닫아 리소스를 해제합니다.
    
    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    """
    db = SessionLocal() # 데이터베이스 세션 생성
    try:
        yield db # 세션 반환
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise e
    finally:
        db.close() # 세션 닫기