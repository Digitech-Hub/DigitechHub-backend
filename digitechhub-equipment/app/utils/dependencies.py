"""
프로젝트 전역에서 사용하는 의존성 주입 유틸리티를 정의합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import AsyncSessionLocal
from .logger import logger
from .jwt_auth import jwt_auth


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    비동기 데이터베이스 세션을 생성하고 반환하는 제너레이터 함수입니다.
    사용 후 세션을 닫아 리소스를 해제합니다.

    Yields:
        AsyncSession: 비동기 SQLAlchemy 데이터베이스 세션
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db  # 세션 반환
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await db.rollback()
            raise e


# 동기식 데이터베이스 세션은 제거됨 - 비동기만 사용


# JWT 토큰 검증을 위한 Bearer 스키마
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    JWT 토큰에서 현재 사용자 정보를 추출합니다.

    Args:
        credentials: HTTP Bearer 토큰 인증 정보

    Returns:
        dict: 사용자 정보 (username, role 등)

    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    try:
        token = credentials.credentials
        user_info = jwt_auth.get_user_info(token)
        logger.info(
            f"User authenticated: {user_info['username']} with role: {user_info['role']}"
        )
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


def require_role(required_role: str):
    """
    특정 역할이 필요한 엔드포인트를 위한 의존성 팩토리

    Args:
        required_role: 필요한 역할

    Returns:
        callable: 역할 검증 의존성 함수
    """

    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role != required_role:
            logger.warning(
                f"Access denied for user {current_user['username']} with role {user_role}. Required: {required_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}",
            )
        return current_user

    return role_checker
