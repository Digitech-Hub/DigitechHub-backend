from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom import (BadRequestException, NotFoundException,
                                   ValidationException)
from app.schemas.input.rental import RentEquipmentRequest
from app.schemas.output.rental import (ExtendRentalResponse, RentalResponse,
                                       ReturnEquipmentResponse)
from app.services.equipment_status import EquipmentStatusServiceInterface
from app.services.equipments import EquipmentManagementServiceInterface
from app.services.rental_histories import RentalHistoryServiceInterface

from .interface import RentalServiceInterface


class RentalService(RentalServiceInterface):
    def __init__(
        self,
        rental_history_service: RentalHistoryServiceInterface,
        equipment_service: EquipmentManagementServiceInterface,
        equipment_status_service: EquipmentStatusServiceInterface,
    ):
        self.rental_history_service = rental_history_service
        self.equipment_service = equipment_service
        self.equipment_status_service = equipment_status_service

    async def rent_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        user_id: str,
        rent_request: RentEquipmentRequest,
    ) -> RentalResponse:
        async with session.begin():
            equipment = await self.equipment_service.get_public_equipment(
                session, equipment_id=equipment_id
            )

            if equipment.status_info and not equipment.status_info.is_available:
                raise BadRequestException("이미 대여 중인 기자재는 대여할 수 없습니다.")

            user_rental_histories = await self.rental_history_service.get_user_rentals(
                session, user_id=user_id
            )
            if any(
                rental_history.is_overdue
                for rental_history in user_rental_histories.items
            ):
                raise BadRequestException("연체 중인 기자재가 있어 대여할 수 없습니다.")

            rent_status = (
                await self.equipment_status_service.get_equipment_status_by_name(
                    session, "rented"
                )
            )

            # 상태 변경과 히스토리 저장을 하나의 트랜잭션으로 처리
            await self.equipment_service.change_status(
                session, equipment_id=equipment.id, status=rent_status
            )

            result = await self.rental_history_service.save_history(
                session,
                user_id=user_id,
                equipment_id=equipment.id,
                rent_request=rent_request,
            )
            return result

    async def extend_rental_period(
        self,
        session: AsyncSession,
        *,
        rental_id: str,
        user_id: str,
        new_due_date: datetime,
    ) -> ExtendRentalResponse:
        rental = await self.rental_history_service.get_rental_info(
            session, rental_id=rental_id, user_id=user_id
        )
        if not rental:
            raise NotFoundException("대여 이력을 찾을 수 없습니다.")

        if rental.is_returned:
            raise ValidationException("이미 반납된 기자재입니다.")
        if rental.is_overdue:
            raise ValidationException("연체된 기자재는 대여 기간을 연장할 수 없습니다.")
        if not rental.can_extend:
            raise ValidationException("대여 연장은 3회까지 가능합니다.")

        # 연장 기한 검증 (최대 30일)
        if new_due_date > rental.rental_date + timedelta(days=30):
            raise ValidationException("대여 연장은 최대 30일까지만 가능합니다.")

        success = await self.rental_history_service.update_due_date(
            session=session,
            rental_id=rental_id,
            user_id=user_id,
            new_due_date=new_due_date,
            updated_count=rental.extend_count + 1,
        )

        return ExtendRentalResponse(
            success=success,
            message="대여 기간을 연장했습니다.",
            new_due_date=new_due_date,
        )

    async def return_equipment(
        self, session: AsyncSession, *, equipment_id: str, user_id: str
    ) -> ReturnEquipmentResponse:
        """
        기자재를 반납합니다.

        Args:
            session (AsyncSession): SQlAlchemy 비동기 세션.
            equipment_id (str): 반납할 기자재 ID.
            user_id (str): 대여한 사용자 ID.

        Returns:
            ReturnEquipmentResponse: 반납 성공 정보.
        """
        async with session.begin():
            # 활성 대여 이력 확인 (사용자-장비 매칭 및 반납 가능 상태 검증은 하위 서비스가 수행)
            user_rentals = await self.rental_history_service.get_user_rentals(
                session,
                user_id=user_id,
                equipment_id=equipment_id,
                include_returned=False,
                offset=0,
                limit=1,
            )
            if not user_rentals.items:
                raise BadRequestException(
                    "해당 사용자에 대한 활성 대여 이력이 없습니다."
                )

            active_rental_id = user_rentals.items[0].rental_id

            success = await self.rental_history_service.update_returned_status(
                session, rental_id=active_rental_id, user_id=user_id
            )

            available_status = (
                await self.equipment_status_service.get_equipment_status_by_name(
                    session, "available"
                )
            )
            await self.equipment_service.change_status(
                session, equipment_id=equipment_id, status=available_status
            )

            return ReturnEquipmentResponse(
                success=success,
                message="반납이 완료되었습니다.",
            )
