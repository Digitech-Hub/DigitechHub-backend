from typing import Optional, Protocol, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import Equipment


class EquipmentRepositoryInterface(Protocol):
    async def get_equipment_by_id(
        self, session: AsyncSession, equipment_id: str
    ) -> Optional[Equipment]: ...

    async def get_public_equipments(
        self,
        session: AsyncSession,
        query: str | None = "",
        category: str | None = "",
        offset: int = 0,
        limit: int = 10,
    ) -> Sequence[Equipment]: ...

    async def count_public_equipments(
        self, session: AsyncSession, query: str | None = "", category: str | None = ""
    ) -> int: ...

    async def save(self, session: AsyncSession, equipment: Equipment) -> Equipment: ...
