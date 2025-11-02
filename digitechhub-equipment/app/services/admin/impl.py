"""
관리자용 기자재 관리 서비스 구현체

이 모듈은 관리자 권한의 기자재 관리 기능을 구현합니다.
조회, 생성, 수정, 삭제 기능을 제공합니다.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom import ConflictException, NotFoundException
from app.models.equipemnt_type import EquipmentType
from app.models.equipment import Equipment
from app.models.equipment_status import EquipmentStatus
from app.models.rental_history import RentalHistory
from app.repositories.equipment_status.interface import \
    EquipmentStatusRepositoryInterface
from app.repositories.equipments.interface import EquipmentRepositoryInterface
from app.repositories.rental_histories.interface import \
    RentalHistoryRepositoryInterface
from app.schemas.output.equipment import EquipmentInfoResponse
from app.schemas.output.equipment_status import EquipmentStatusInfo
from app.schemas.output.response import Page
from app.services.admin.interface import AdminEquipmentServiceInterface


class AdminEquipmentService(AdminEquipmentServiceInterface):
    """
    관리자용 기자재 관리 서비스 구현체.

    관리자 권한의 기자재 CRUD 작업을 수행합니다.
    """

    def __init__(
        self,
        equipment_repository: EquipmentRepositoryInterface,
        equipment_status_repository: EquipmentStatusRepositoryInterface,
        rental_history_repository: RentalHistoryRepositoryInterface,
    ):
        self.equipment_repository = equipment_repository
        self.equipment_status_repository = equipment_status_repository
        self.rental_history_repository = rental_history_repository

    def _to_equipment_info_response(self, eq: Equipment) -> EquipmentInfoResponse:
        """Equipment 모델을 EquipmentInfoResponse로 변환."""
        eq_status = eq.equipment_status
        return EquipmentInfoResponse(
            id=eq.id,
            alias=eq.alias,
            status_info=(
                EquipmentStatusInfo(
                    id=eq_status.id,
                    name=eq_status.name,
                    display_name=eq_status.display_name,
                    description=eq_status.description,
                    is_available=eq_status.is_available,
                    is_active=eq_status.is_active,
                    color_code=eq_status.color_code,
                )
                if eq_status
                else None
            ),
            type=eq.equipment_type.name if eq.equipment_type else None,
        )

    # Query methods
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
        """관리자용 기자재 목록 조회."""
        from sqlalchemy import func, or_

        # 기본 쿼리 구성
        base_query = select(Equipment)
        count_query = select(func.count(Equipment.id))

        # 비공개 포함 여부
        if not include_private:
            base_query = base_query.where(Equipment.is_public)
            count_query = count_query.where(Equipment.is_public)

        # 검색어 필터
        if query and query.strip():
            query_filter = or_(
                Equipment.alias.contains(query.strip()),
                Equipment.info_comment.contains(query.strip()),
                Equipment.admin_comment.contains(query.strip()),
            )
            base_query = base_query.where(query_filter)
            count_query = count_query.where(query_filter)

        # 카테고리 필터
        if category and category.strip():
            base_query = base_query.join(EquipmentType).where(
                EquipmentType.name == category.strip()
            )
            count_query = count_query.join(EquipmentType).where(
                EquipmentType.name == category.strip()
            )

        # 상태 필터
        if status and status.strip():
            base_query = base_query.join(EquipmentStatus).where(
                EquipmentStatus.name == status.strip()
            )
            count_query = count_query.join(EquipmentStatus).where(
                EquipmentStatus.name == status.strip()
            )

        # 페이지네이션
        base_query = base_query.offset(offset).limit(limit)

        # 실행
        result = await session.execute(base_query)
        equipments = result.scalars().all()

        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        # 변환
        items = [self._to_equipment_info_response(eq) for eq in equipments]

        return Page[EquipmentInfoResponse](
            items=items, total=total, offset=offset, limit=limit
        )

    async def get_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
    ) -> EquipmentInfoResponse:
        """관리자용 기자재 상세 조회."""
        eq = await self.equipment_repository.get_equipment_by_id(
            session, equipment_id
        )
        if not eq:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        return self._to_equipment_info_response(eq)

    # Creation methods
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
        """새로운 기자재 생성."""
        # 유형 확인
        type_query = select(EquipmentType).where(EquipmentType.id == equipment_type_id)
        type_result = await session.execute(type_query)
        equipment_type = type_result.scalar_one_or_none()
        if not equipment_type:
            raise NotFoundException(
                message="기자재 유형을 찾을 수 없습니다",
                details={"equipment_type_id": equipment_type_id},
            )

        # 상태 확인
        status_query = select(EquipmentStatus).where(
            EquipmentStatus.id == equipment_status_id
        )
        status_result = await session.execute(status_query)
        equipment_status = status_result.scalar_one_or_none()
        if not equipment_status:
            raise NotFoundException(
                message="기자재 상태를 찾을 수 없습니다",
                details={"equipment_status_id": equipment_status_id},
            )

        # 기자재 생성
        equipment = Equipment(
            alias=alias,
            equipment_type_id=equipment_type_id,
            equipment_status_id=equipment_status_id,
            is_public=is_public,
            admin_comment=admin_comment,
            info_comment=info_comment,
        )

        equipment = await self.equipment_repository.save(session, equipment)
        await session.commit()

        return self._to_equipment_info_response(equipment)

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
        """새로운 기자재 유형 생성."""
        # 중복 확인
        existing_query = select(EquipmentType).where(EquipmentType.name == name)
        existing_result = await session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise ConflictException(
                message="이미 존재하는 기자재 유형입니다",
                details={"name": name},
            )

        # 유형 생성
        equipment_type = EquipmentType(
            name=name,
            description=description,
            is_public=is_public,
            comment=comment,
            equipment_image=equipment_image,
        )

        session.add(equipment_type)
        await session.commit()
        await session.refresh(equipment_type)

        return {
            "id": equipment_type.id,
            "name": equipment_type.name,
            "description": equipment_type.description,
            "is_public": equipment_type.is_public,
            "comment": equipment_type.comment,
            "equipment_image": equipment_type.equipment_image,
        }

    async def create_rental_history(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
        user_id: str,
        due_date: str,
        admin_comment: Optional[str] = None,
    ) -> dict:
        """관리자용 대여 이력 생성."""
        # 기자재 확인
        equipment = await self.equipment_repository.get_equipment_by_id(
            session, equipment_id
        )
        if not equipment:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        # 이미 대여 중인지 확인
        active_rental = await self.rental_history_repository.get_active_rental_by_equipment(
            session, equipment_id
        )
        if active_rental:
            raise ConflictException(
                message="이미 대여 중인 기자재입니다",
                details={"equipment_id": equipment_id},
            )

        # 대여 이력 생성
        due_date_dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        rental_history = RentalHistory(
            equipment_id=equipment_id,
            user_id=user_id,
            due_date=due_date_dt,
        )

        rental_history = await self.rental_history_repository.save(
            session, rental_history
        )

        # 기자재 상태를 'rented'로 변경
        status = await self.equipment_status_repository.get_equipment_status_by_name(
            session, "rented"
        )
        if status:
            equipment.change_status(status)
            await self.equipment_repository.save(session, equipment)

        await session.commit()

        return {
            "id": rental_history.id,
            "equipment_id": rental_history.equipment_id,
            "user_id": rental_history.user_id,
            "rental_date": rental_history.rental_date.isoformat(),
            "due_date": rental_history.due_date.isoformat(),
            "is_returned": rental_history.is_returned,
        }

    # Modification methods
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
        """기자재 정보 업데이트."""
        equipment = await self.equipment_repository.get_equipment_by_id(
            session, equipment_id
        )
        if not equipment:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        # 유형 업데이트
        if equipment_type_id is not None:
            type_query = select(EquipmentType).where(
                EquipmentType.id == equipment_type_id
            )
            type_result = await session.execute(type_query)
            if not type_result.scalar_one_or_none():
                raise NotFoundException(
                    message="기자재 유형을 찾을 수 없습니다",
                    details={"equipment_type_id": equipment_type_id},
                )
            equipment.equipment_type_id = equipment_type_id

        # 상태 업데이트
        if equipment_status_id is not None:
            status_query = select(EquipmentStatus).where(
                EquipmentStatus.id == equipment_status_id
            )
            status_result = await session.execute(status_query)
            if not status_result.scalar_one_or_none():
                raise NotFoundException(
                    message="기자재 상태를 찾을 수 없습니다",
                    details={"equipment_status_id": equipment_status_id},
                )
            equipment.equipment_status_id = equipment_status_id

        # 나머지 필드 업데이트
        if alias is not None:
            equipment.alias = alias
        if is_public is not None:
            equipment.is_public = is_public
        if admin_comment is not None:
            equipment.admin_comment = admin_comment
        if info_comment is not None:
            equipment.info_comment = info_comment

        await self.equipment_repository.save(session, equipment)
        await session.commit()

        return self._to_equipment_info_response(equipment)

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
        """기자재 상태 정보 업데이트."""
        status_query = select(EquipmentStatus).where(EquipmentStatus.id == status_id)
        status_result = await session.execute(status_query)
        status = status_result.scalar_one_or_none()

        if not status:
            raise NotFoundException(
                message="기자재 상태를 찾을 수 없습니다",
                details={"status_id": status_id},
            )

        # 필드 업데이트
        if name is not None:
            status.name = name
        if display_name is not None:
            status.display_name = display_name
        if description is not None:
            status.description = description
        if priority is not None:
            status.priority = priority
        if is_available is not None:
            status.is_available = is_available
        if is_active is not None:
            status.is_active = is_active
        if color_code is not None:
            status.color_code = color_code

        session.add(status)
        await session.commit()

        return {
            "id": status.id,
            "name": status.name,
            "display_name": status.display_name,
            "description": status.description,
            "priority": status.priority,
            "is_available": status.is_available,
            "is_active": status.is_active,
            "color_code": status.color_code,
        }

    async def update_rental_history(
        self,
        session: AsyncSession,
        *,
        rental_history_id: str,
        due_date: Optional[str] = None,
        return_date: Optional[str] = None,
        is_returned: Optional[bool] = None,
        extend_count: Optional[int] = None,
        admin_comment: Optional[str] = None,
    ) -> dict:
        """관리자용 대여 이력 수정."""
        # 대여 이력 조회
        rental_query = select(RentalHistory).where(
            RentalHistory.id == rental_history_id
        )
        rental_result = await session.execute(rental_query)
        rental = rental_result.scalar_one_or_none()

        if not rental:
            raise NotFoundException(
                message="대여 이력을 찾을 수 없습니다",
                details={"rental_history_id": rental_history_id},
            )

        # 필드 업데이트
        if due_date is not None:
            rental.due_date = datetime.fromisoformat(
                due_date.replace("Z", "+00:00")
            )
        if is_returned is not None:
            rental.is_returned = is_returned
            if is_returned:
                rental.return_date = datetime.now()
                # 기자재 상태를 'available'로 변경
                equipment = await self.equipment_repository.get_equipment_by_id(
                    session, rental.equipment_id
                )
                if equipment:
                    status = (
                        await self.equipment_status_repository.get_equipment_status_by_name(
                            session, "available"
                        )
                    )
                    if status:
                        equipment.change_status(status)
                        await self.equipment_repository.save(session, equipment)
            else:
                rental.return_date = None
        if extend_count is not None:
            rental.extend_count = extend_count

        session.add(rental)
        await session.commit()

        return {
            "id": rental.id,
            "equipment_id": rental.equipment_id,
            "user_id": rental.user_id,
            "rental_date": rental.rental_date.isoformat(),
            "due_date": rental.due_date.isoformat(),
            "return_date": rental.return_date.isoformat() if rental.return_date else None,
            "is_returned": rental.is_returned,
            "extend_count": rental.extend_count,
        }

    # Deletion methods
    async def delete_equipment(
        self,
        session: AsyncSession,
        *,
        equipment_id: str,
    ) -> None:
        """기자재 삭제."""
        equipment = await self.equipment_repository.get_equipment_by_id(
            session, equipment_id
        )
        if not equipment:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        # 대여 중인지 확인
        active_rental = await self.rental_history_repository.get_active_rental_by_equipment(
            session, equipment_id
        )
        if active_rental:
            raise ConflictException(
                message="대여 중인 기자재는 삭제할 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        await session.delete(equipment)
        await session.commit()

    async def delete_equipment_type(
        self,
        session: AsyncSession,
        *,
        equipment_type_id: str,
    ) -> None:
        """기자재 유형 삭제."""
        # 유형 확인
        type_query = select(EquipmentType).where(EquipmentType.id == equipment_type_id)
        type_result = await session.execute(type_query)
        equipment_type = type_result.scalar_one_or_none()

        if not equipment_type:
            raise NotFoundException(
                message="기자재 유형을 찾을 수 없습니다",
                details={"equipment_type_id": equipment_type_id},
            )

        # 해당 유형을 사용하는 기자재 확인
        equipments_query = select(Equipment).where(
            Equipment.equipment_type_id == equipment_type_id
        )
        equipments_result = await session.execute(equipments_query)
        equipments = equipments_result.scalars().all()

        if equipments:
            raise ConflictException(
                message="해당 유형을 사용하는 기자재가 존재합니다",
                details={
                    "equipment_type_id": equipment_type_id,
                    "count": len(equipments),
                },
            )

        await session.delete(equipment_type)
        await session.commit()
