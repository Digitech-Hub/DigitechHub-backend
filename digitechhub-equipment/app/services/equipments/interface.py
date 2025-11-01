from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.output.equipment import EquipmentInfoResponse
from app.schemas.output.equipment_status import EquipmentStatusInfo
from app.schemas.output.response import Page


@runtime_checkable
class EquipmentQueryServiceInterface(Protocol):
    """
    장비 조회 서비스의 인터페이스 정의.

    이 인터페이스는 장비 목록 조회 및 상세 조회 기능을 비동기 방식으로 제공합니다.
    """

    async def get_public_equipment_list(
        self,
        session: AsyncSession,
        *,
        query: str | None = "",
        category: str | None = "",
        offset: int = 0,
        limit: int = 10,
    ) -> Page[EquipmentInfoResponse]:
        """
        공개된 장비 목록을 조회합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            query (str): 검색어.
            category (str): 장비 카테고리.
            offset (int): 페이지 오프셋. 기본값은 0입니다.
            limit (int): 페이지 크기. 기본값은 10입니다.

        Returns:
            Page[EquipmentInfoResponse]: 장비 정보 응답의 페이지 객체.
        """
        ...

    async def get_public_equipment(
        self, session: AsyncSession, *, equipment_id: str
    ) -> EquipmentInfoResponse:
        """
        공개된 특정 장비의 상세 정보를 조회합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            equipment_id (str): 조회할 장비 ID.

        Returns:
            EquipmentInfoResponse: 장비 정보 응답 객체.
        """
        ...


@runtime_checkable
class EquipmentManagementServiceInterface(EquipmentQueryServiceInterface, Protocol):
    """
    장비 대여 서비스의 통합 인터페이스.
    """

    async def change_status(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        status: EquipmentStatusInfo,
    ) -> None:
        """
        특정 장비의 상태를 변경합니다.

        Args:
            session (AsyncSession): SQLAlchemy 비동기 세션.
            equipment_id (str): 상태를 변경할 장비 ID.
            status (EquipmentStatusInfo): 설정할 상태 정보.
        """
        ...
