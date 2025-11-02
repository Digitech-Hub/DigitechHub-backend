from datetime import datetime
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.input.rental import RentEquipmentRequest
from app.schemas.output.rental import (ExtendRentalResponse, RentalResponse,
                                       ReturnEquipmentResponse)


@runtime_checkable
class RentalCreationServiceInterface(Protocol):
    """
    Equipment 도메인과 Rental History 도메인에 대한 생성이 동시에 이루어지는 로직의 서비스 레이어 인터페이스입니다.
    """

    async def rent_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        user_id: str,
        rent_request: RentEquipmentRequest,
    ) -> RentalResponse:
        """
        장비를 대여합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            equipment_id (str): 대여할 기자재 ID.
            user_id (str): 대여할 사용자 ID.

        Returns:
            RentalResponse: 대여 정보.
        """
        ...


@runtime_checkable
class RentalModificationServiceInterface(Protocol):
    """
    기자재 반납, 대여 기간 연장 등 Equipment 도메인과 Rental History 도메인에
    대한 수정이 이루어지는 서비스 인터페이스입니다.
    """

    async def extend_rental_period(
        self,
        session: AsyncSession,
        *,
        rental_id: str,
        user_id: str,
        new_due_date: datetime,
    ) -> ExtendRentalResponse:
        """
        장비 대여 기간을 연장합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            rental_id (str): 연장할 대여 기록 ID.
            user_id (str): 대여한 사용자 ID.
            new_due_date (datetime): 새로운 반납 예정일.

        Returns:
            ExtendRentalResponse: 연장된 대여 기록 정보.
        """
        ...

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
        ...


@runtime_checkable
class RentalServiceInterface(
    RentalCreationServiceInterface,
    RentalModificationServiceInterface,
    Protocol,
):
    """
    Equipment 도메인과 Rental History 도메인에 대한 조회, 생성, 수정이
    동시에 이루어지는 로직을 처리하는 통합 서비스 인터페이스입니다.
    """
