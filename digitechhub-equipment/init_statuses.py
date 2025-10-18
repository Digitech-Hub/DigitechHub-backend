#!/usr/bin/env python3
"""
기자재 상태 초기화 스크립트
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.status_initializer import EquipmentStatusInitializer

def init_statuses():
    """기본 기자재 상태들을 초기화합니다."""
    try:
        print("Initializing default equipment statuses...")
        
        # 동기식 엔진 생성 (상태 초기화용)
        sync_database_url = os.environ.get("DATABASE_URL", "mysql+pymysql://root:password@digitechhub-mysql:3306/digitechhub_equipment")
        sync_engine = create_engine(sync_database_url)
        SyncSessionLocal = sessionmaker(bind=sync_engine)
        
        with SyncSessionLocal() as sync_session:
            EquipmentStatusInitializer.initialize_default_statuses(sync_session)
            print("Default equipment statuses initialized successfully!")
        
    except Exception as e:
        print(f"Error during status initialization: {e}")
        raise

if __name__ == "__main__":
    init_statuses()