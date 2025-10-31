from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom import NotFoundException, ValidationException
from app.models.rental_history import RentalHistory
from app.repositories.rental_histories.interface import \
    RentalHistoryRepositoryInterface
from app.schemas.input.rental import RentEquipmentRequest
from app.schemas.output.equipment import (EquipmentInfoResponse,
                                          EquipmentStatusInfo)
from app.schemas.output.rental import RentalResponse
from app.schemas.output.rental_history import (RentalDetailInfo,
                                               RentalHistoryResponse)
from app.schemas.output.response import Page
from app.services.rental_histories.interface import \
    RentalHistoryServiceInterface


class RentalHistoryService(RentalHistoryServiceInterface):
    def __init__(self, rental_repository: RentalHistoryRepositoryInterface):
        self.rental_repository = rental_repository

    @staticmethod
    def _validate_due_date(current_date: datetime, due_date: datetime) -> datetime:
        """대여 기한 검증 (현재 시각 이후, 최대 30일)"""
        if due_date <= current_date:
            raise ValidationException("반환 기한은 현재 시간 이후여야 합니다.")
        if due_date > current_date + timedelta(days=30):
            raise ValidationException("반환 기한은 최대 30일 이내여야 합니다.")
        return due_date

    async def save_history(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        equipment_id: str,
        rent_request: RentEquipmentRequest,
    ) -> RentalResponse:
        current_date = datetime.now(tz=timezone.utc)
        valid_due_date = self._validate_due_date(current_date, rent_request.due_date)

        rental_history = RentalHistory(
            equipment_id=equipment_id,
            user_id=user_id,
            rental_date=current_date,
            due_date=valid_due_date,
            is_returned=False,
            extend_count=0,
        )

        saved_rental = await self.rental_repository.save(session, rental_history)

        # Refetch with relationships to build response
        rental_with_equipment = await self.rental_repository.get_rental_history_by_id(
            session, saved_rental.id, saved_rental.user_id
        )
        
        if not rental_with_equipment:
            raise NotFoundException("대여 기록을 찾을 수 없습니다.")

        # Build EquipmentInfoResponse with proper structure
        eq_status = rental_with_equipment.equipment.equipment_status
        equipment = EquipmentInfoResponse(
            id=rental_with_equipment.equipment_id,
            alias=rental_with_equipment.equipment.alias,
            status_info=EquipmentStatusInfo(
                id=eq_status.id,
                name=eq_status.name,
                display_name=eq_status.display_name,
                description=eq_status.description,
                is_available=eq_status.is_available,
                is_active=eq_status.is_active,
                color_code=eq_status.color_code,
            ) if eq_status else None,
            type=rental_with_equipment.equipment.equipment_type.name if rental_with_equipment.equipment.equipment_type else None,
        )

        return RentalResponse(
            success=True,
            message="성공적으로 기자재를 대여했습니다.",
            equipment=equipment,
        )

    async def get_user_rentals(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        start_date_range: datetime | None = None,
        end_date_range: datetime | None = None,
        equipment_id: str | None = None,
        include_returned: bool = False,
        search: str = "",
        offset: int = 0,
        limit: int = 10,
    ) -> Page[RentalHistoryResponse]:
        if start_date_range and end_date_range and start_date_range > end_date_range:
            raise ValidationException("날짜 검색 범위가 올바르지 않습니다.")

        rentals = await self.rental_repository.get_rentals_by_user(
            session=session,
            user_id=user_id,
            start_date_range=start_date_range,
            end_date_range=end_date_range,
            equipment_id=equipment_id,
            include_returned=include_returned,
            search=search,
            offset=offset,
            limit=limit,
        )
        total = await self.rental_repository.count_user_rentals(
            session=session,
            user_id=user_id,
            start_date_range=start_date_range,
            end_date_range=end_date_range,
            equipment_id=equipment_id,
            include_returned=include_returned,
            search=search,
        )

        items = [
            RentalHistoryResponse(
                rental_id=rental.id,
                equipment_id=rental.equipment_id,
                user_id=rental.user_id,
                rental_date=rental.rental_date,
                due_date=rental.due_date,
                return_date=rental.return_date,
                is_returned=rental.is_returned,
                is_overdue=rental.is_overdue,
            )
            for rental in rentals
        ]

        return Page[RentalHistoryResponse](
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_rental_info(
        self, session: AsyncSession, *, rental_id: str, user_id: str
    ) -> RentalDetailInfo:
        rental = await self.rental_repository.get_rental_history_by_id(
            session, rental_id, user_id
        )
        if not rental:
            raise NotFoundException("대여 이력을 찾을 수 없습니다.")

        now = datetime.now(tz=timezone.utc)
        days_remaining = (
            max((rental.due_date - now).days, 0) if not rental.is_returned else 0
        )

        # Convert Equipment model to EquipmentInfoResponse
        eq_status = rental.equipment.equipment_status
        equipment_response = EquipmentInfoResponse(
            id=rental.equipment_id,
            alias=rental.equipment.alias,
            status_info=EquipmentStatusInfo(
                id=eq_status.id,
                name=eq_status.name,
                display_name=eq_status.display_name,
                description=eq_status.description,
                is_available=eq_status.is_available,
                is_active=eq_status.is_active,
                color_code=eq_status.color_code,
            ) if eq_status else None,
            type=rental.equipment.equipment_type.name if rental.equipment.equipment_type else None,
        )

        # Calculate rental duration in days
        rental_duration_days = (rental.due_date - rental.rental_date).days

        return RentalDetailInfo(
            rental_id=rental.id,
            equipment=equipment_response,
            rental_date=rental.rental_date,
            due_date=rental.due_date,
            return_date=rental.return_date,
            is_returned=rental.is_returned,
            rental_duration=rental_duration_days,
            days_remaining=days_remaining,
            is_overdue=rental.is_overdue,
            can_extend=rental.can_extend,
            extend_count=rental.extend_count,
        )

    async def update_due_date(
        self,
        session: AsyncSession,
        rental_id: str,
        user_id: str,
        new_due_date: datetime,
        updated_count: int,
    ) -> bool:
        """대여 만료일을 업데이트합니다."""
        success = await self.rental_repository.update_due_date(
            session, rental_id, user_id, new_due_date, updated_count
        )
        return success

    async def update_returned_status(
        self, session: AsyncSession, *, rental_id: str, user_id: str
    ) -> bool:
        rental = await self.rental_repository.get_rental_history_by_id(
            session, rental_id, user_id
        )
        if not rental:
            raise NotFoundException("대여 이력을 찾을 수 없습니다.")
        if rental.is_returned:
            raise ValidationException("이미 반납된 기자재입니다.")

        success = await self.rental_repository.update_status_to_return(
            session, rental_id, user_id
        )
        return success
