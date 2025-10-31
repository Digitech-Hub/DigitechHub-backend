from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom import NotFoundException
from app.repositories.equipment_status import \
    EquipmentStatusRepositoryInterface
from app.schemas.output.equipment_status import EquipmentStatusInfo

from .interface import EquipmentStatusServiceInterface


class EquipmentStatusService(EquipmentStatusServiceInterface):
    def __init__(self, equipment_status_repository: EquipmentStatusRepositoryInterface):
        self.equipment_status_repository = equipment_status_repository

    async def get_equipment_status_by_name(
        self, session: AsyncSession, status_name: str
    ) -> EquipmentStatusInfo:
        status = await self.equipment_status_repository.get_equipment_status_by_name(
            session, status_name
        )
        if not status:
            raise NotFoundException("기자재 상태 정보를 찾을 수 없습니다.")

        return EquipmentStatusInfo(
            id=status.id,
            name=status.name,
            display_name=status.display_name,
            description=status.description,
            is_available=status.is_available,
            is_active=status.is_active,
            color_code=status.color_code,
        )
