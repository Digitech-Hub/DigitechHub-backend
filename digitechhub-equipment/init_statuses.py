#!/usr/bin/env python3
"""
기자재 상태 초기화 스크립트

이 스크립트를 실행하여 데이터베이스에 기본 기자재 상태들을 생성합니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.utils.database import get_database
from app.utils.status_initializer import EquipmentStatusInitializer


def main():
    """메인 함수"""
    print("기자재 상태 초기화를 시작합니다...")
    
    try:
        # 데이터베이스 세션 생성
        db_session = next(get_database())
        
        # 기본 상태들 초기화
        statuses = EquipmentStatusInitializer.initialize_default_statuses(db_session)
        
        print(f"\n초기화 완료! {len(statuses)}개의 상태가 생성되었습니다:")
        for status in statuses:
            print(f"  - {status.display_name} ({status.name}) - {'대여 가능' if status.is_available else '대여 불가'}")
        
        db_session.close()
        print("\n기자재 상태 초기화가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
