from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.equipment import Equipment
from app.models.rental_history import RentalHistory

from .interface import RentalHistoryRepositoryInterface


class RentalHistoryRepository(RentalHistoryRepositoryInterface):
    def _apply_filters(
        self,
        query,
        *,
        user_id: str,
        start_date_range: Optional[datetime] = None,
        end_date_range: Optional[datetime] = None,
        equipment_id: Optional[str] = None,
        include_returned: bool = False,
    ):
        """검색어 제외 필터링 전용"""
        query = query.where(RentalHistory.user_id == user_id)
        if not include_returned:
            query = query.where(RentalHistory.is_returned.is_(False))
        if start_date_range:
            query = query.where(RentalHistory.rental_date >= start_date_range)
        if end_date_range:
            query = query.where(RentalHistory.rental_date <= end_date_range)
        if equipment_id:
            query = query.where(RentalHistory.equipment_id == equipment_id)
        return query

    def _apply_search(self, query, search: str):
        """검색어 기반 join + ilike 처리 (select 전용)"""
        if search:
            query = (
                query.join(RentalHistory.equipment)
                .where(Equipment.alias.ilike(f"%{search}%"))
                .options(selectinload(RentalHistory.equipment))
            )
        return query

    async def get_active_rental_by_equipment(
        self, session: AsyncSession, equipment_id: str
    ) -> Optional[RentalHistory]:
        query = select(RentalHistory).where(
            RentalHistory.equipment_id == equipment_id,
            RentalHistory.is_returned.is_(False),
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_rentals_by_user(
        self,
        session: AsyncSession,
        user_id: str,
        start_date_range: Optional[datetime] = None,
        end_date_range: Optional[datetime] = None,
        equipment_id: Optional[str] = None,
        include_returned: bool = False,
        search: str = "",
        offset: int = 0,
        limit: int = 10,
    ) -> List[RentalHistory]:
        query = self._apply_filters(
            select(RentalHistory),
            user_id=user_id,
            start_date_range=start_date_range,
            end_date_range=end_date_range,
            equipment_id=equipment_id,
            include_returned=include_returned,
        )
        query = self._apply_search(query, search)
        query = query.order_by(
            RentalHistory.created_at.asc(), RentalHistory.due_date.asc()
        )
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    async def save(self, session: AsyncSession, rental: RentalHistory) -> RentalHistory:
        session.add(rental)
        await session.flush()
        return rental

    async def count_user_rentals(
        self,
        session: AsyncSession,
        user_id: str,
        start_date_range: Optional[datetime] = None,
        end_date_range: Optional[datetime] = None,
        equipment_id: Optional[str] = None,
        include_returned: bool = False,
        search: str = "",
    ) -> int:
        query = self._apply_filters(
            select(func.count()).select_from(RentalHistory),
            user_id=user_id,
            start_date_range=start_date_range,
            end_date_range=end_date_range,
            equipment_id=equipment_id,
            include_returned=include_returned,
        )

        if search:
            query = query.join(RentalHistory.equipment).where(
                Equipment.alias.ilike(f"%{search}%")
            )

        result = await session.execute(query)
        return result.scalar_one()

    async def get_rental_history_by_id(
        self, session: AsyncSession, rental_id: str, user_id: str
    ) -> Optional[RentalHistory]:
        query = (
            select(RentalHistory)
            .where(RentalHistory.id == rental_id, RentalHistory.user_id == user_id)
            .options(
                selectinload(RentalHistory.equipment).selectinload(Equipment.equipment_status),
                selectinload(RentalHistory.equipment).selectinload(Equipment.equipment_type),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def update_due_date(
        self,
        session: AsyncSession,
        rental_id: str,
        user_id: str,
        new_due_date: datetime,
        updated_count: int,
    ) -> bool:
        query = (
            update(RentalHistory)
            .where(RentalHistory.id == rental_id, RentalHistory.user_id == user_id)
            .values(extend_count=updated_count, due_date=new_due_date)
        )
        result = await session.execute(query)
        await session.flush()
        return result.rowcount > 0

    async def update_status_to_return(
        self, session: AsyncSession, rental_id: str, user_id: str
    ) -> bool:
        query = (
            update(RentalHistory)
            .where(RentalHistory.id == rental_id, RentalHistory.user_id == user_id)
            .values(is_returned=True)
        )
        result = await session.execute(query)
        await session.flush()
        return result.rowcount > 0
