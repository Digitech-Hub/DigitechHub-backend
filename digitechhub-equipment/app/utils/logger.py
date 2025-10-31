"""
로깅 설정 모듈
"""

import logging
import sys


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    로거 인스턴스를 생성하고 반환합니다.
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 중복 설정 방지
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.propagate = False  # 상위 로거로 전파 방지
    
    return logger

# 기본 로거 인스턴스
logger = get_logger(__name__)