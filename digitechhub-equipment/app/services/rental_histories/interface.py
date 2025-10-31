from datetime import datetime
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.input.rental import RentEquipmentRequest
from app.schemas.output.rental import RentalResponse
from app.schemas.output.rental_history import (RentalDetailInfo,
                                               RentalHistoryResponse)
from app.schemas.output.response import Page


@runtime_checkable
class RentalHistoryQueryServiceInterface(Protocol):
    """
    장비 대여 이력 조회 서비스의 인터페이스 정의.

    이 인터페이스는 장비 대여 이력 조회 기능을 비동기 방식으로 제공합니다.
    """

    async def get_user_rentals(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        start_date_range: datetime | None = None,
        end_date_range: datetime | None = None,
        equipment_id: str | None = None,
        include_returned: bool = False,
        offset: int = 0,
        limit: int = 10,
        search: str = ""
    ) -> Page[RentalHistoryResponse]:
        """
        특정 사용자의 대여 이력을 조회합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            user_id (str): 사용자 ID.
            start_date_range (datetime | None): 검색할 대여 시작 일자 범위.
            end_date_range (datetime | None): 검색할 대여 시작 일자 범위.
            equipment_id (str | None): 검색할 기자재 아이디.
            offset (int): 페이지 오프셋. 기본값은 0입니다.
            limit (int): 페이지 크기. 기본값은 10입니다.

        Returns:
            Page[RentalResponse]: 사용자의 대여 이력 목록.
        """
        ...

    async def get_rental_info(
        self, session: AsyncSession, *, rental_id: str, user_id: str
    ) -> RentalDetailInfo:
        """
        특정 대여 이력의 상세 정보를 조회합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            rental_id (str): 조회할 대여 이력 ID.
            user_id (str): 조회하는 사용자 ID.

        Returns:
            RentalDetailInfo: 대여 이력 상세 정보.
        """
        ...


@runtime_checkable
class RentalHistoryCreationServiceInterface(Protocol):
    """
    장비 대여 이력 추가 서비스의 인터페이스 정의.

    이 인터페이스는 장비 대여 기록 저장 기능을 비동기 방식으로 제공합니다.
    """

    async def save_history(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        equipment_id: str,
        rent_request: RentEquipmentRequest
    ) -> RentalResponse:
        """
        장비 대여 기록을 저장합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            user_id (str): 대여하는 사용자 ID.
            equipment_id (str): 대여할 장비 ID.
            rent_request (RentEquipmentRequest): 대여 요청 정보.

        Returns:
            RentalResponse: 저장된 대여 기록 정보.
        """
        ...


@runtime_checkable
class RentalHistoryModificationServiceInterface(Protocol):
    """
    장비 대여 이력 수정 서비스의 인터페이스 정의.

    이 인터페이스는 장비 대여 이력의 수정 기능을 비동기 방식으로 제공합니다.
    """

    async def update_due_date(
        self,
        session: AsyncSession,
        rental_id: str,
        user_id: str,
        new_due_date: datetime,
        updated_count: int,
    ) -> bool:
        """
        대여 만료일을 업데이트합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            rental_id (str): 업데이트할 대여 기록 ID.
            user_id (str): 대여한 사용자 ID.
            new_due_date (datetime): 새로운 만료일.
            updated_count (int): 업데이트된 연장 횟수.

        Returns:
            bool: 업데이트 성공 여부.
        """
        ...

    async def update_returned_status(
        self, session: AsyncSession, *, rental_id: str, user_id: str
    ) -> bool:
        """
        대여 이력의 상태를 반납 상태로 업데이트합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            rental_id (str): 연장할 대여 기록 ID.
            user_id (str): 대여한 사용자 ID.

        Returns:
            bool: 업데이트 성공 여부.
        """
        ...


@runtime_checkable
class RentalHistoryServiceInterface(
    RentalHistoryQueryServiceInterface,
    RentalHistoryCreationServiceInterface,
    RentalHistoryModificationServiceInterface,
    Protocol,
):
    """
    장비 대여 이력 서비스의 통합 인터페이스 정의.

    이 인터페이스는 장비 대여 이력 조회, 대여 이력 수정등의 기능을 비동기 방식으로 제공합니다.
    """
