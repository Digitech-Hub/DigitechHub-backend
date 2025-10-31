"""
Equipment 서비스

기자재 대여 서비스의 비즈니스 로직을 수행합니다.

Classes:
    - EquipmentManagementService: 기자재 비즈니스 로직 클래스

Interfaces:
    - EquipmentManagementServiceInterface: 기자재 비즈니스 로직 인터페이스
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom import NotFoundException
from app.models.equipment import Equipment
from app.repositories.equipment_status.interface import \
    EquipmentStatusRepositoryInterface
from app.repositories.equipments.interface import EquipmentRepositoryInterface
from app.schemas.output.equipment import (EquipmentInfoResponse,
                                          EquipmentStatusInfo)
from app.schemas.output.response import Page
from app.services.equipments.interface import \
    EquipmentManagementServiceInterface


class EquipmentManagementService(EquipmentManagementServiceInterface):
    """
    기자재 비즈니스 로직 클래스

    Attributes:
        equipment_repository (EquipmentRepositoryInterface): 기자재 리포지토리
    """

    def __init__(
        self,
        equipment_repository: EquipmentRepositoryInterface,
        equipment_status_repository: EquipmentStatusRepositoryInterface,
    ):
        self.equipment_repository = equipment_repository
        self.equipment_status_repository = equipment_status_repository

    def _to_equipment_info_response(self, eq: Equipment) -> EquipmentInfoResponse:
        eq_status = eq.equipment_status
        return EquipmentInfoResponse(
            id=eq.id,
            alias=eq.alias,
            status_info=(
                EquipmentStatusInfo(
                    id=eq_status.id,
                    name=eq_status.name,
                    display_name=eq_status.display_name,
                    description=eq_status.description,
                    is_available=eq_status.is_available,
                    is_active=eq_status.is_active,
                    color_code=eq_status.color_code,
                )
                if eq_status
                else None
            ),
            type=eq.equipment_type.name if eq.equipment_type else None,
        )

    async def get_public_equipment_list(
        self,
        session: AsyncSession,
        *,
        query: str = "",
        category: str = "",
        offset: int = 0,
        limit: int = 10,
    ) -> Page[EquipmentInfoResponse]:
        equipments = await self.equipment_repository.get_public_equipments(
            session, query, category, offset, limit
        )
        total = await self.equipment_repository.count_public_equipments(
            session, query, category
        )
        items = [self._to_equipment_info_response(eq) for eq in equipments]

        return Page[EquipmentInfoResponse](
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_public_equipment(
        self, session: AsyncSession, *, equipment_id: str
    ) -> EquipmentInfoResponse:
        eq = await self.equipment_repository.get_equipment_by_id(session, equipment_id)
        if not eq or not eq.is_public:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        return self._to_equipment_info_response(eq)

    async def change_status(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        status: EquipmentStatusInfo,
    ) -> None:
        eq = await self.equipment_repository.get_equipment_by_id(session, equipment_id)
        if not eq:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        status_entity = await self.equipment_status_repository.get_equipment_status_by_name(
            session, status.name
        )
        if not status_entity:
            raise NotFoundException(
                message="기자재 상태 정보를 찾을 수 없습니다.",
                details={"status_name": status.name},
            )

        eq.change_status(status_entity)
        await self.equipment_repository.save(session, eq)
