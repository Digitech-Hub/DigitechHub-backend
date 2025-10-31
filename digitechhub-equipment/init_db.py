#!/usr/bin/env python3
"""
데이터베이스 테이블 초기화 스크립트
"""

import asyncio
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, '/app')

from app.models.abstract_base import Base
from app.utils.database import async_engine


async def init_database():
    """데이터베이스 테이블을 생성하고 초기 데이터를 삽입합니다."""
    try:
        print("Creating database tables...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully!")
        
        # 기본 상태 데이터 초기화는 별도로 실행
        print("Default equipment statuses will be initialized separately.")
        
        print("Database initialization completed!")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())
