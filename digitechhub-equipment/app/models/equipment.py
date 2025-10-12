from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.models.abstract_base import AbstractBaseModel

if TYPE_CHECKING:
    from app.models.rental_history import RentalHistory
    from app.models.equipemnt_type import EquipmentType
    from app.models.equipment_status import EquipmentStatus


class Equipment(AbstractBaseModel):
    """
    기자재 모델

    주요 기능:
    - 장비 이름, 설명, 상태 필드
    - 장비 유형과의 다대일 관계 설정
    """

    __tablename__ = "equipments"

    alias: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="기자재 별칭"
    )
    equipment_status_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("equipment_statuses.id"),
        nullable=False,
        comment="기자재 상태 ID",
    )
    equipment_type_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("equipment_types.id"),
        nullable=False,
        comment="기자재 유형 ID",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="공개 여부"
    )
    admin_comment: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="관리자 전용 코멘트"
    )
    info_comment: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="유의사항 및 정보"
    )

    # 기자재 상태와의 다대일 관계 설정
    equipment_status: Mapped["EquipmentStatus"] = relationship(
        "EquipmentStatus", back_populates="equipments"
    )

    # 기자재 유형과의 다대일 관계 설정
    equipment_type: Mapped["EquipmentType"] = relationship(
        "EquipmentType", back_populates="equipments"
    )

    # 대여 이력과의 일대다 관계 설정
    rental_histories: Mapped[list["RentalHistory"]] = relationship(
        "RentalHistory", back_populates="equipment", cascade="all, delete-orphan"
    )

    # 테이블별 고유 인덱스
    __table_args__ = (
        Index('ix_equipments_created_at', 'created_at'),
        Index('ix_equipments_updated_at', 'updated_at'),
        Index('ix_equipments_equipment_status_id', 'equipment_status_id'),
        Index('ix_equipments_equipment_type_id', 'equipment_type_id'),
    )

    def __repr__(self) -> str:
        return f"<Equipment(id={self.id}, status={self.equipment_status.name if self.equipment_status else 'Unknown'}, alias={self.alias})>"

    def __str__(self) -> str:
        return self.alias or f"Equipment({self.id})"
    
    @property
    def status(self) -> str:
        """상태 이름을 반환하는 프로퍼티 (하위 호환성을 위해)"""
        return self.equipment_status.name if self.equipment_status else "unknown"
