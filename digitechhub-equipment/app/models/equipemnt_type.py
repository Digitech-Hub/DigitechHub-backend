from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract_base import AbstractBaseModel

if TYPE_CHECKING:
    from app.models.equipment import Equipment


class EquipmentType(AbstractBaseModel):
    """
    기자재 유형 모델

    주요 기능:
    - 장비 유형 이름 및 설명 필드
    - 장비와의 일대다 관계 설정
    - 계산된 카운트는 별도 뷰나 쿼리로 처리 (데이터 일관성 보장)
    """

    __tablename__ = "equipment_types"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="기자재 유형"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="기자재 유형 설명"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="공개 여부"
    )
    comment: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="추가 설명"
    )
    equipment_image: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="기자재 이미지 URL"
    )

    # 장비와의 일대다 관계 설정
    equipments: Mapped[list["Equipment"]] = relationship(
        "Equipment", back_populates="equipment_type", cascade="all, delete-orphan"
    )

    # 테이블별 고유 인덱스
    __table_args__ = (
        Index('ix_equipment_types_created_at', 'created_at'),
        Index('ix_equipment_types_updated_at', 'updated_at'),
        Index('ix_equipment_types_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<EquipmentType(id={self.id}, name={self.name})>"

    def __str__(self) -> str:
        return self.name
    
    @property
    def total_count(self) -> int:
        """해당 유형의 총 기자재 수 (계산된 값)"""
        return len(self.equipments)
    
    @property
    def available_count(self) -> int:
        """사용 가능한 기자재 수 (계산된 값)"""
        return len([eq for eq in self.equipments if eq.equipment_status and eq.equipment_status.name == "available"])
    
    @property
    def broken_count(self) -> int:
        """고장난 기자재 수 (계산된 값)"""
        return len([eq for eq in self.equipments if eq.equipment_status and eq.equipment_status.name == "broken"])
    
    @property
    def rented_count(self) -> int:
        """대여 중인 기자재 수 (계산된 값)"""
        return len([eq for eq in self.equipments if eq.equipment_status and eq.equipment_status.name == "rented"])
    
    @property
    def maintenance_count(self) -> int:
        """수리 중인 기자재 수 (계산된 값)"""
        return len([eq for eq in self.equipments if eq.equipment_status and eq.equipment_status.name == "maintenance"])
    
    @property
    def total_rentals(self) -> int:
        """총 대여 횟수 (계산된 값)"""
        return sum(len(eq.rental_histories) for eq in self.equipments)
