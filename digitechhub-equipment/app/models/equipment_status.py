from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract_base import AbstractBaseModel

if TYPE_CHECKING:
    from app.models.equipment import Equipment


class EquipmentStatus(AbstractBaseModel):
    """
    기자재 상태 모델
    
    주요 기능:
    - 기자재의 다양한 상태를 정의 (available, rented, broken, maintenance 등)
    - 상태별 우선순위와 설명 관리
    - 기자재와의 일대다 관계 설정
    """
    
    __tablename__ = "equipment_statuses"
    
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="상태 이름"
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="표시용 상태 이름"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="상태 설명"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="상태 우선순위 (낮을수록 높은 우선순위)"
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="대여 가능 여부"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="활성 상태 여부"
    )
    color_code: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True, comment="UI용 색상 코드 (#RRGGBB)"
    )
    
    # 기자재와의 일대다 관계 설정
    equipments: Mapped[list["Equipment"]] = relationship(
        "Equipment", back_populates="equipment_status", cascade="all, delete-orphan"
    )
    
    # 테이블별 고유 인덱스
    __table_args__ = (
        Index('ix_equipment_statuses_created_at', 'created_at'),
        Index('ix_equipment_statuses_updated_at', 'updated_at'),
        Index('ix_equipment_statuses_name', 'name'),
        Index('ix_equipment_statuses_priority', 'priority'),
        Index('ix_equipment_statuses_is_available', 'is_available'),
        Index('ix_equipment_statuses_is_active', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<EquipmentStatus(id={self.id}, name={self.name}, display_name={self.display_name})>"
    
    def __str__(self) -> str:
        return self.display_name
    
    @property
    def equipment_count(self) -> int:
        """이 상태의 기자재 수 (계산된 값)"""
        return len(self.equipments)
    
    @property
    def available_equipment_count(self) -> int:
        """대여 가능한 기자재 수 (이 상태가 대여 가능한 경우)"""
        if not self.is_available:
            return 0
        return len([eq for eq in self.equipments if eq.is_public])
