from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, ForeignKey, func, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract_base import AbstractBaseModel

if TYPE_CHECKING:
    from app.models.equipment import Equipment


class RentalHistory(AbstractBaseModel):
    """
    대여 이력 모델
    
    주요 기능:
    - 기자재 대여 및 반납 이력 관리
    - 사용자별 대여 기록 추적
    """
    
    __tablename__ = "rental_histories"

    equipment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("equipments.id"),
        nullable=False,
        comment="기자재 ID",
    )
    user_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="SSO 사용자 ID",
    )
    rental_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="대여 날짜"
    )
    return_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="반납 날짜",
    )
    is_returned: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="반납 여부"
    )

    # 기자재와의 다대일 관계 설정
    equipment: Mapped["Equipment"] = relationship(
        "Equipment", back_populates="rental_histories"
    )
    
    # 테이블별 고유 인덱스
    __table_args__ = (
        Index('ix_rental_histories_created_at', 'created_at'),
        Index('ix_rental_histories_updated_at', 'updated_at'),
        Index('ix_rental_histories_equipment_id', 'equipment_id'),
        Index('ix_rental_histories_user_id', 'user_id'),
        Index('ix_rental_histories_is_returned', 'is_returned'),
    )
    
    def __repr__(self) -> str:
        return f"<RentalHistory(id={self.id}, equipment_id={self.equipment_id}, user_id={self.user_id})>"
