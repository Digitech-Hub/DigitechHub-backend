"""
관리자용 기자재 관리 서비스 인터페이스

이 모듈은 관리자 권한의 기자재 조회, 생성, 수정, 삭제를 위한
서비스 인터페이스들을 정의합니다.

관리자는 일반 사용자에게는 제공되지 않는 다음 기능들을 사용할 수 있습니다:
- 비공개 기자재 조회 및 관리
- 기자재 생성, 수정, 삭제
- 기자재 유형 관리
- 대여 이력 수정
"""

from typing import Optional, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.output.equipment import EquipmentInfoResponse
from app.schemas.output.response import Page


@runtime_checkable
class AdminEquipmentQueryServiceInterface(Protocol):
    """
    관리자 권한의 기자재 조회 서비스 인터페이스.

    일반 사용자 서비스와 달리, 관리자는 다음 기능을 제공받습니다:
    - 비공개 기자재 포함 조회
    - 상태별 필터링
    - 관리자 코멘트 포함 상세 조회
    """

    async def get_equipment_list(
        self,
        session: AsyncSession,
        *,
        query: Optional[str] = "",
        category: Optional[str] = "",
        status: Optional[str] = "",
        include_private: bool = True,
        offset: int = 0,
        limit: int = 10,
    ) -> Page[EquipmentInfoResponse]:
        """
        관리자용 기자재 목록 조회.

        Args:
            session: SQLAlchemy 비동기 세션
            query: 검색어 (기자재 별칭, 코멘트에서 검색)
            category: 기자재 유형 필터 (기자재 유형 이름)
            status: 기자재 상태 필터 (상태 이름)
            include_private: 비공개 기자재 포함 여부 (기본값: True)
            offset: 페이지 오프셋 (기본값: 0)
            limit: 페이지 크기 (기본값: 10)

        Returns:
            Page[EquipmentInfoResponse]: 기자재 정보 페이지 객체

        Note:
            - 일반 사용자 API와 달리 include_private=True일 때 비공개 기자재도 포함
            - status 필터는 기자재 상태의 name 필드를 기준으로 필터링
        """
        ...

    async def get_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
    ) -> EquipmentInfoResponse:
        """
        관리자용 기자재 상세 정보 조회.

        Args:
            session: SQLAlchemy 비동기 세션
            equipment_id: 조회할 기자재 ID

        Returns:
            EquipmentInfoResponse: 기자재 정보 응답 객체

        Note:
            - 일반 사용자 API와 달리 비공개 기자재도 조회 가능
            - 관리자 코멘트(admin_comment)가 포함된 정보 제공
        """
        ...


@runtime_checkable
class AdminEquipmentCreationServiceInterface(Protocol):
    """
    관리자용 기자재 생성 서비스 인터페이스.

    관리자만 기자재를 생성할 수 있으며, 다음 작업을 수행할 수 있습니다:
    - 새로운 기자재 생성
    - 기자재 유형 생성
    - 대여 이력 생성 (특수 케이스용)
    """

    async def create_equipment(
        self,
        session: AsyncSession,
        *,
        alias: Optional[str],
        equipment_type_id: str,
        equipment_status_id: str,
        is_public: bool = True,
        admin_comment: Optional[str] = None,
        info_comment: Optional[str] = None,
    ) -> EquipmentInfoResponse:
        """
        새로운 기자재 생성.

        Args:
            session: SQLAlchemy 비동기 세션
            alias: 기자재 별칭
            equipment_type_id: 기자재 유형 ID
            equipment_status_id: 초기 기자재 상태 ID
            is_public: 공개 여부 (기본값: True)
            admin_comment: 관리자 전용 코멘트
            info_comment: 유의사항 및 정보

        Returns:
            EquipmentInfoResponse: 생성된 기자재 정보

        Raises:
            NotFoundException: equipment_type_id 또는 equipment_status_id가 존재하지 않는 경우
        """
        ...

    async def create_equipment_type(
        self,
        session: AsyncSession,
        *,
        name: str,
        description: Optional[str] = None,
        is_public: bool = True,
        comment: Optional[str] = None,
        equipment_image: Optional[str] = None,
    ) -> dict:
        """
        새로운 기자재 유형 생성.

        Args:
            session: SQLAlchemy 비동기 세션
            name: 기자재 유형 이름
            description: 기자재 유형 설명
            is_public: 공개 여부 (기본값: True)
            comment: 추가 설명
            equipment_image: 기자재 이미지 URL

        Returns:
            dict: 생성된 기자재 유형 정보

        Raises:
            ConflictException: 동일한 name을 가진 유형이 이미 존재하는 경우
        """
        ...

    async def create_rental_history(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        user_id: str,
        due_date: str,  # ISO 8601 datetime string
        admin_comment: Optional[str] = None,
    ) -> dict:
        """
        관리자용 대여 이력 생성 (특수 케이스용).

        일반적인 대여는 일반 사용자 API를 통해 처리되며,
        이 메서드는 관리자가 직접 대여 이력을 생성해야 하는 경우에만 사용됩니다.

        Args:
            session: SQLAlchemy 비동기 세션
            equipment_id: 대여할 기자재 ID
            user_id: 대여자 사용자 ID
            due_date: 대여 만료 날짜 (ISO 8601 형식)
            admin_comment: 관리자 코멘트

        Returns:
            dict: 생성된 대여 이력 정보

        Raises:
            NotFoundException: equipment_id가 존재하지 않거나 대여 불가능한 상태인 경우
            ConflictException: 이미 대여 중인 기자재인 경우

        Note:
            - 자동으로 rental_date를 현재 시간으로 설정
            - 기자재 상태를 'rented'로 변경
        """
        ...


@runtime_checkable
class AdminEquipmentModificationServiceInterface(Protocol):
    """
    관리자용 기자재 수정 서비스 인터페이스.

    관리자만 기자재 정보를 수정할 수 있으며, 다음 작업을 수행할 수 있습니다:
    - 기자재 정보 업데이트
    - 기자재 상태 관리
    - 대여 이력 수정
    """

    async def update_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        alias: Optional[str] = None,
        equipment_type_id: Optional[str] = None,
        equipment_status_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        admin_comment: Optional[str] = None,
        info_comment: Optional[str] = None,
    ) -> EquipmentInfoResponse:
        """
        기자재 정보 업데이트.

        Args:
            session: SQLAlchemy 비동기 세션
            equipment_id: 수정할 기자재 ID
            alias: 기자재 별칭 (옵션)
            equipment_type_id: 기자재 유형 ID (옵션)
            equipment_status_id: 기자재 상태 ID (옵션)
            is_public: 공개 여부 (옵션)
            admin_comment: 관리자 코멘트 (옵션)
            info_comment: 유의사항 및 정보 (옵션)

        Returns:
            EquipmentInfoResponse: 수정된 기자재 정보

        Raises:
            NotFoundException: equipment_id, equipment_type_id, 또는 equipment_status_id가
                              존재하지 않는 경우

        Note:
            - 제공된 필드만 업데이트 (partial update)
            - None으로 제공된 필드는 기존 값 유지
        """
        ...

    async def update_equipment_status(
        self,
        session: AsyncSession,
        *,
        status_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        is_available: Optional[bool] = None,
        is_active: Optional[bool] = None,
        color_code: Optional[str] = None,
    ) -> dict:
        """
        기자재 상태 정보 업데이트.

        Args:
            session: SQLAlchemy 비동기 세션
            status_id: 수정할 상태 ID
            name: 상태 이름 (옵션)
            display_name: 표시용 상태 이름 (옵션)
            description: 상태 설명 (옵션)
            priority: 우선순위 (옵션)
            is_available: 대여 가능 여부 (옵션)
            is_active: 활성 상태 여부 (옵션)
            color_code: UI용 색상 코드 (옵션)

        Returns:
            dict: 수정된 기자재 상태 정보

        Raises:
            NotFoundException: status_id가 존재하지 않는 경우

        Note:
            - is_active가 False로 변경되면 해당 상태로 기자재를 변경할 수 없음
        """
        ...

    async def update_rental_history(
        self,
        session: AsyncSession,
        *,
        rental_history_id: str,
        due_date: Optional[str] = None,  # ISO 8601 datetime string
        return_date: Optional[str] = None,  # ISO 8601 datetime string
        is_returned: Optional[bool] = None,
        extend_count: Optional[int] = None,
        admin_comment: Optional[str] = None,
    ) -> dict:
        """
        관리자용 대여 이력 수정 (특수 케이스용).

        Args:
            session: SQLAlchemy 비동기 세션
            rental_history_id: 수정할 대여 이력 ID
            due_date: 대여 만료 날짜 (옵션, ISO 8601 형식)
            return_date: 반납 날짜 (옵션, ISO 8601 형식)
            is_returned: 반납 여부 (옵션)
            extend_count: 연장 횟수 (옵션)
            admin_comment: 관리자 코멘트 (옵션)

        Returns:
            dict: 수정된 대여 이력 정보

        Raises:
            NotFoundException: rental_history_id가 존재하지 않는 경우

        Note:
            - is_returned=True로 설정하면 자동으로 return_date를 현재 시간으로 설정
            - is_returned=False로 설정하면 return_date를 None으로 설정
            - 반납 처리 시 기자재 상태를 'available'로 변경
        """
        ...


@runtime_checkable
class AdminEquipmentDeletionServiceInterface(Protocol):
    """
    관리자용 기자재 삭제 서비스 인터페이스.

    관리자만 기자재를 삭제할 수 있습니다.
    """

    async def delete_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
    ) -> None:
        """
        기자재 삭제.

        Args:
            session: SQLAlchemy 비동기 세션
            equipment_id: 삭제할 기자재 ID

        Raises:
            NotFoundException: equipment_id가 존재하지 않는 경우
            ConflictException: 대여 중인 기자재인 경우

        Note:
            - 대여 중(is_returned=False)인 기자재는 삭제 불가
            - 삭제 시 관련 대여 이력도 함께 삭제됨 (cascade)
        """
        ...

    async def delete_equipment_type(
        self,
        session: AsyncSession,
        *,
        equipment_type_id: str,
    ) -> None:
        """
        기자재 유형 삭제.

        Args:
            session: SQLAlchemy 비동기 세션
            equipment_type_id: 삭제할 기자재 유형 ID

        Raises:
            NotFoundException: equipment_type_id가 존재하지 않는 경우
            ConflictException: 해당 유형을 사용하는 기자재가 존재하는 경우

        Note:
            - 해당 유형을 사용하는 기자재가 있을 경우 삭제 불가
        """
        ...


@runtime_checkable
class AdminEquipmentServiceInterface(
    AdminEquipmentQueryServiceInterface,
    AdminEquipmentCreationServiceInterface,
    AdminEquipmentModificationServiceInterface,
    AdminEquipmentDeletionServiceInterface,
    Protocol,
):
    """
    관리자용 기자재 통합 서비스 인터페이스.

    모든 관리자 권한의 기자재 관리 기능을 통합한 인터페이스입니다.
    조회, 생성, 수정, 삭제 기능을 모두 포함합니다.

    구현 클래스:
        - AdminEquipmentService: 관리자 기자재 서비스 구현체
    """

    pass
