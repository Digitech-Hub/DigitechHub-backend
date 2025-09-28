"""
모든 데이터베이스 엔티티를 위한 추상 기본 모델

이 모듈은 모든 모델에 대해 UUID, 타임스탬프와 같은
표준 필드를 포함하는 공통 기본 클래스를 제공합니다.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class AbstractBaseModel(Base):
    """
    모든 데이터베이스 엔티티에 공통 필드를 제공하는 추상 기본 모델입니다.
    
    이 클래스는 직접 인스턴스화하면 안 됩니다. 대신 다른 모델들이
    이 클래스를 상속받아 공통 기능을 사용해야 합니다.
    
    주요 기능:
    - UUID 기본 키
    - 자동 타임스탬프 관리
    - 데이터베이스 레벨 인덱싱
    """
    
    __abstract__ = True

    # UUID 기본 키
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID 기본 키 식별자"
    )
    
    # 생성 타임스탬프 (데이터베이스에서 자동 설정)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="레코드 생성 타임스탬프"
    )
    
    # 수정 타임스탬프 (데이터베이스에서 자동 업데이트)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="레코드 마지막 수정 타임스탬프"
    )
    
    def __repr__(self) -> str:
        """
        모델 인스턴스의 문자열 표현을 반환합니다.
        
        Returns:
            str: 사람이 읽을 수 있는 표현
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
