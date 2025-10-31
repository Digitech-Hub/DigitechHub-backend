from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.output.equipment_status import EquipmentStatusInfo


class EquipmentStatusQueryServiceInterface(Protocol):
    async def get_equipment_status_by_name(
        self, session: AsyncSession, status_name: str
    ) -> EquipmentStatusInfo: ...


class EquipmentStatusServiceInterface(EquipmentStatusQueryServiceInterface, Protocol):
    """"""
