"""
기자재 상태 초기화 유틸리티

데이터베이스에 기본 기자재 상태들을 생성합니다.
"""

from sqlalchemy.orm import Session

from app.models.equipment_status import EquipmentStatus


class EquipmentStatusInitializer:
    """
    기자재 상태 초기화 클래스
    """

    DEFAULT_STATUSES = [
        {
            "name": "available",
            "display_name": "사용 가능",
            "description": "대여 가능한 상태",
            "priority": 1,
            "is_available": True,
            "is_active": True,
            "color_code": "#28a745",  # 녹색
        },
        {
            "name": "rented",
            "display_name": "대여 중",
            "description": "현재 대여된 상태",
            "priority": 2,
            "is_available": False,
            "is_active": True,
            "color_code": "#007bff",  # 파란색
        },
        {
            "name": "maintenance",
            "display_name": "수리 중",
            "description": "점검 및 수리가 필요한 상태",
            "priority": 3,
            "is_available": False,
            "is_active": True,
            "color_code": "#ffc107",  # 노란색
        },
        {
            "name": "broken",
            "display_name": "고장",
            "description": "사용할 수 없는 상태",
            "priority": 4,
            "is_available": False,
            "is_active": True,
            "color_code": "#dc3545",  # 빨간색
        },
        {
            "name": "retired",
            "display_name": "폐기",
            "description": "더 이상 사용하지 않는 상태",
            "priority": 5,
            "is_available": False,
            "is_active": False,
            "color_code": "#6c757d",  # 회색
        },
    ]

    @classmethod
    def initialize_default_statuses(cls, session: Session) -> list[EquipmentStatus]:
        """
        기본 기자재 상태들을 초기화합니다.

        Args:
            session: 데이터베이스 세션

        Returns:
            list[EquipmentStatus]: 생성된 상태 목록
        """
        created_statuses = []

        for status_data in cls.DEFAULT_STATUSES:
            # 이미 존재하는지 확인
            existing_status = (
                session.query(EquipmentStatus)
                .filter(EquipmentStatus.name == status_data["name"])
                .first()
            )

            if existing_status:
                # 기존 상태 업데이트
                for key, value in status_data.items():
                    setattr(existing_status, key, value)
                created_statuses.append(existing_status)
                print(f"Updated existing status: {status_data['display_name']}")
            else:
                # 새 상태 생성
                new_status = EquipmentStatus(**status_data)
                session.add(new_status)
                created_statuses.append(new_status)
                print(f"Created new status: {status_data['display_name']}")

        try:
            session.commit()
            print(
                f"Successfully initialized {len(created_statuses)} equipment statuses"
            )
            return created_statuses
        except Exception as e:
            session.rollback()
            print(f"Failed to initialize equipment statuses: {e}")
            raise

    @classmethod
    def get_status_by_name(cls, session: Session, name: str) -> EquipmentStatus | None:
        """
        이름으로 기자재 상태를 조회합니다.

        Args:
            session: 데이터베이스 세션
            name: 상태 이름

        Returns:
            EquipmentStatus | None: 조회된 상태 또는 None
        """
        return (
            session.query(EquipmentStatus).filter(EquipmentStatus.name == name).first()
        )

    @classmethod
    def get_available_statuses(cls, session: Session) -> list[EquipmentStatus]:
        """
        대여 가능한 상태들을 조회합니다.

        Args:
            session: 데이터베이스 세션

        Returns:
            list[EquipmentStatus]: 대여 가능한 상태 목록
        """
        return (
            session.query(EquipmentStatus)
            .filter(EquipmentStatus.is_available, EquipmentStatus.is_active)
            .order_by(EquipmentStatus.priority)
            .all()
        )

    @classmethod
    def get_all_active_statuses(cls, session: Session) -> list[EquipmentStatus]:
        """
        모든 활성 상태들을 조회합니다.

        Args:
            session: 데이터베이스 세션

        Returns:
            list[EquipmentStatus]: 활성 상태 목록
        """
        return (
            session.query(EquipmentStatus)
            .filter(EquipmentStatus.is_active)
            .order_by(EquipmentStatus.priority)
            .all()
        )
