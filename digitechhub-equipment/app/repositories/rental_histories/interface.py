from datetime import datetime
from typing import List, Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rental_history import RentalHistory


class RentalHistoryRepositoryInterface(Protocol):
    async def get_active_rental_by_equipment(
        self, session: AsyncSession, equipment_id: str
    ) -> Optional[RentalHistory]: ...

    async def get_rentals_by_user(
        self,
        session: AsyncSession,
        user_id: str,
        start_date_range: datetime | None,
        end_date_range: datetime | None,
        equipment_id: str | None,
        include_returned: bool = False,
        search: str = "",
        offset: int = 0,
        limit: int = 10,
    ) -> List[RentalHistory]: ...

    async def save(
        self, session: AsyncSession, rental: RentalHistory
    ) -> RentalHistory: ...

    async def count_user_rentals(
        self,
        session: AsyncSession,
        user_id: str,
        start_date_range: datetime | None,
        end_date_range: datetime | None,
        equipment_id: str | None,
        include_returned: bool = False,
        search: str = "",
    ) -> int: ...

    async def get_rental_history_by_id(
        self, session: AsyncSession, rental_id: str, user_id: str
    ) -> Optional[RentalHistory]: ...

    async def update_due_date(
        self,
        session: AsyncSession,
        rental_id: str,
        user_id: str,
        new_due_date: datetime,
        updated_count: int,
    ) -> bool: ...

    async def update_status_to_return(
        self, session: AsyncSession, rental_id: str, user_id: str
    ) -> bool: ...
