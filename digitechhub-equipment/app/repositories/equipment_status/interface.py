from typing import Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment_status import EquipmentStatus


class EquipmentStatusRepositoryInterface(Protocol):
    async def get_equipment_status_by_name(
        self, session: AsyncSession, name: str
    ) -> Optional[EquipmentStatus]:
        """
        name을 통해 EquipmentStatus를 조회합니다.

        Args:
            session (AsyncSession): SQLAlchemy 세션
            name (str): 검색한 Equipment Status의 이름

        Returns:
            Optional[EquipmentStatus]: 검색된 EquipmentStatus
        """
        ...
