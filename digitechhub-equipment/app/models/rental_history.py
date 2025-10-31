from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, Index,
                        Integer, String, func)
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
        comment="대여 날짜",
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="대여 만료 날짜"
    )
    return_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="반납 날짜",
    )
    is_returned: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="반납 여부"
    )
    extend_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="연장 횟수"
    )

    # 기자재와의 다대일 관계 설정
    equipment: Mapped["Equipment"] = relationship(
        "Equipment", back_populates="rental_histories"
    )

    # 테이블별 고유 인덱스
    __table_args__ = (
        Index("ix_rental_histories_created_at", "created_at"),
        Index("ix_rental_histories_updated_at", "updated_at"),
        Index("ix_rental_histories_equipment_id", "equipment_id"),
        Index("ix_rental_histories_user_id", "user_id"),
        Index("ix_rental_histories_is_returned", "is_returned"),
        CheckConstraint(
            "(is_returned = 0 AND return_date IS NULL) OR (is_returned = 1 AND return_date IS NOT NULL)",
            name="ck_return_status_consistency",
        ),
    )

    def __repr__(self) -> str:
        return f"<RentalHistory(id={self.id}, equipment_id={self.equipment_id}, user_id={self.user_id})>"

    @property
    def is_overdue(self) -> bool:
        """대여 만료 여부를 반환합니다."""
        if self.is_returned:
            return False
        return True if func.now() > self.due_date else False

    @property
    def can_extend(self) -> bool:
        """
        연장 가능 여부를 반환합니다.
        3회 이하 연장 가능
        """
        return self.extend_count <= 3
