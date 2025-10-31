from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment_status import EquipmentStatus

from .interface import EquipmentStatusRepositoryInterface


class EquipmentStatusRepository(EquipmentStatusRepositoryInterface):

    async def get_equipment_status_by_name(
        self, session: AsyncSession, name: str
    ) -> Optional[EquipmentStatus]:
        query = select(EquipmentStatus).where(EquipmentStatus.name == name)
        result = await session.execute(query)

        return result.scalar_one_or_none()
