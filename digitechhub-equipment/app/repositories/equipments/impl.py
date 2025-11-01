from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.equipemnt_type import EquipmentType
from app.models.equipment import Equipment

from .interface import EquipmentRepositoryInterface


class EquipmentRepository(EquipmentRepositoryInterface):
    async def get_equipment_by_id(self, session: AsyncSession, equipment_id: str) -> Optional[Equipment]:
        query = select(Equipment).where(Equipment.id == equipment_id).options(selectinload(Equipment.equipment_status))
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_public_equipments(self, session: AsyncSession, query: str | None = "", category: str | None = "", offset: int = 0, limit: int = 10) -> Sequence[Equipment]:
        base_query = select(Equipment).where(Equipment.is_public)

        if query and query.strip():
            query_filter = or_(
                Equipment.alias.contains(query.strip()),
                Equipment.info_comment.contains(query.strip()),
            )
            base_query = base_query.where(query_filter)

        if category and category.strip():
            base_query = base_query.join(EquipmentType).where(EquipmentType.name == category.strip())
        
        base_query = base_query.offset(offset).limit(limit)
        result = await session.execute(base_query)
        return result.scalars().all()

    async def count_public_equipments(self, session: AsyncSession, query: str | None = "", category: str | None = "") -> int:
        count_query = select(func.count(Equipment.id)).where(Equipment.is_public)
        
        if query and query.strip():
            query_filter = or_(
                Equipment.alias.contains(query.strip()),
                Equipment.info_comment.contains(query.strip()),
            )
            count_query = count_query.where(query_filter)
        
        if category and category.strip():
            count_query = count_query.join(EquipmentType).where(EquipmentType.name == category.strip())
        
        result = await session.execute(count_query)
        return result.scalar_one()

    async def save(self, session: AsyncSession, equipment: Equipment) -> Equipment:
        session.add(equipment)
        return equipment