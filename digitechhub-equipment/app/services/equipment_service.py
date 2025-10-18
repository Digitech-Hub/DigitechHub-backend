"""
Equipment 서비스

기자재 관련 비즈니스 로직을 수행합니다.
"""

import datetime
from sqlalchemy import text, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, RentalHistory, EquipmentStatus
from app.decorators import get_execution_time_decorator
from app.exceptions import NotFoundException, ValidationException
from app.schemas import RentEquipmentRequest


class EquipmentService:
    """
    기자재 비즈니스 로직 클래스
    """

    @staticmethod
    async def get_database_status(session: AsyncSession):
        result = await session.execute(text("SELECT 1 as test"))
        return result.fetchone()

    @staticmethod
    @get_execution_time_decorator
    async def get_public_equipment_list(
        query: str, category: str, session: AsyncSession
    ) -> list[dict]:
        """
        공개된 기자재 목록을 조회합니다.

        Args:
            query: 기자재 검색어 (alias, info_comment에서 검색)
            category: 기자재 유형 카테고리 (equipment_type.name으로 필터링)
            session: 데이터베이스 세션

        Returns:
            list[dict]: 공개된 기자재 목록
        """
        from app.models.equipemnt_type import EquipmentType

        # 기본 쿼리: is_public이 True인 기자재들만 조회
        base_query = select(Equipment).where(Equipment.is_public == True)

        # query 매개변수가 있으면 검색 필터 적용
        if query and query.strip():
            query_filter = or_(
                Equipment.alias.contains(query.strip()),
                Equipment.info_comment.contains(query.strip()),
            )
            base_query = base_query.where(query_filter)

        # category 매개변수가 있으면 카테고리 필터 적용
        if category and category.strip():
            base_query = base_query.join(EquipmentType).where(
                EquipmentType.name == category.strip()
            )

        result = await session.execute(base_query)
        results = result.scalars().all()
        equipment_list = []

        for eq in results:
            equipment_list.append(
                {
                    "id": eq.id,
                    "alias": eq.alias,
                    "type": eq.equipment_type.name if eq.equipment_type else None,
                    "status": eq.status,
                    "status_display": (
                        eq.equipment_status.display_name
                        if eq.equipment_status
                        else None
                    ),
                    "created_at": eq.created_at.isoformat() if eq.created_at else None,
                    "updated_at": eq.updated_at.isoformat() if eq.updated_at else None,
                }
            )

        return equipment_list

    @staticmethod
    @get_execution_time_decorator
    async def get_public_equipment(equipment_id: str, session: AsyncSession) -> dict:
        """
        인자로 받은 equipment_id를 통해 해당하는 기자재를 조회합니다.

        Args:
            equipment_id: 기자재 고유 아이디
            session: 데이터베이스 세션

        Returns:
            dict: 조회된 기자재
        """
        query = select(Equipment).where(
            Equipment.is_public == True,
            Equipment.id == equipment_id
        )
        result = await session.execute(query)
        result = result.scalar_one_or_none()

        if not result:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={
                    "equipment_id": equipment_id,
                },
            )

        return {
            "id": result.id,
            "alias": result.alias,
            "type": result.equipment_type.name if result.equipment_type else None,
            "status": result.status,
            "status_display": (
                result.equipment_status.display_name
                if result.equipment_status
                else None
            ),
            "comment": result.info_comment,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        }

    @staticmethod
    @get_execution_time_decorator
    async def rent_equipment(
        equipment_id: str,
        rent_equipment_request: RentEquipmentRequest,
        user_id: str,
        session: AsyncSession,
    ) -> dict:
        """
        기자재 상태를 확인한 후, 사용자에게 권한이 있다면 대여 이력을 생성한 후,
        기자재 상태를 업데이트해 대여 처리를 합니다.

        Args:
            equipment_id: 기자재 고유 아이디
            user_id: 사용자 아이디 ( JWT Token Claim )
            session: 데이터베이스 세션

        Returns:
            dict: 대여된 기자재, 대여 성공 여부
        """
        query = select(Equipment).where(
            Equipment.is_public == True,
            Equipment.id == equipment_id
        )
        result = await session.execute(query)
        db_equipment = result.scalar_one_or_none()

        if not db_equipment:
            raise NotFoundException(
                message="해당하는 기자재를 찾을 수 없습니다",
                details={
                    "equipment_id": equipment_id,
                },
            )

        current_date = datetime.datetime.now()

        # due_date가 현재 날짜보다 이전인지 검증
        if rent_equipment_request.due_date <= current_date:
            raise ValidationException(
                message="대여 만료일은 현재 날짜보다 이후여야 합니다",
                details={
                    "input_due_date": rent_equipment_request.due_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "current_date": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "equipment_id": equipment_id,
                },
            )

        # 기자재가 이미 대여 중인지 확인
        rental_query = select(RentalHistory).where(
            RentalHistory.equipment_id == equipment_id,
            RentalHistory.is_returned == False,
        )
        rental_result = await session.execute(rental_query)
        active_rental = rental_result.scalar_one_or_none()

        if active_rental:
            raise ValidationException(
                message="해당 기자재는 이미 대여 중입니다",
                details={
                    "equipment_id": equipment_id,
                    "current_renter": active_rental.user_id,
                    "rental_date": active_rental.rental_date.isoformat(),
                },
            )

        # 기자재 상태가 대여 가능한지 확인
        if (
            not db_equipment.equipment_status
            or not db_equipment.equipment_status.is_available
        ):
            raise ValidationException(
                message="해당 기자재는 현재 대여할 수 없습니다",
                details={
                    "equipment_id": equipment_id,
                    "current_status": db_equipment.status,
                    "status_display": (
                        db_equipment.equipment_status.display_name
                        if db_equipment.equipment_status
                        else "Unknown"
                    ),
                },
            )

        # 대여 이력 생성
        rent_model = RentalHistory(
            equipment_id=equipment_id,
            user_id=user_id,
            due_date=rent_equipment_request.due_date,
            rental_date=current_date,
            is_returned=False,
        )

        # 기자재 상태를 'rented'로 업데이트
        status_query = select(EquipmentStatus).where(EquipmentStatus.name == "rented")
        status_result = await session.execute(status_query)
        rented_status = status_result.scalar_one_or_none()
        if not rented_status:
            raise ValidationException(
                message="대여 상태를 찾을 수 없습니다",
                details={"equipment_id": equipment_id},
            )

        db_equipment.equipment_status_id = rented_status.id
        db_equipment.updated_at = current_date

        # 데이터베이스에 저장
        session.add(rent_model)
        await session.commit()
        await session.refresh(rent_model)

        return {
            "rental_history": {
                "id": rent_model.id,
                "equipment_id": rent_model.equipment_id,
                "user_id": rent_model.user_id,
                "rental_date": rent_model.rental_date.isoformat(),
                "due_date": rent_model.due_date.isoformat(),
                "is_returned": rent_model.is_returned,
            },
            "equipment": {
                "id": db_equipment.id,
                "alias": db_equipment.alias,
                "status": db_equipment.status,
                "type": (
                    db_equipment.equipment_type.name
                    if db_equipment.equipment_type
                    else None
                ),
                "status_display": (
                    db_equipment.equipment_status.display_name
                    if db_equipment.equipment_status
                    else None
                ),
            },
        }

    @staticmethod
    @get_execution_time_decorator
    async def get_rentals_equipment(session: AsyncSession, user_id: str) -> dict:
        """
        사용자의 현재 대여 중 기자재 목록을 조회합니다.

        Args:
            session: 데이터베이스 세션
            user_id: 사용자 아이디

        Returns:
            dict: 대여 중인 기자재 목록과 상세 정보
        """
        # 현재 대여 중인 기자재 이력 조회 (반납되지 않은 것들)
        rental_query = select(RentalHistory).where(
            RentalHistory.user_id == user_id,
            RentalHistory.is_returned == False
        )
        rental_result = await session.execute(rental_query)
        db_rental_histories = rental_result.scalars().all()

        if not db_rental_histories:
            return {
                "message": "현재 대여 중인 기자재가 없습니다",
                "rentals": [],
                "total_count": 0,
            }

        rentals_list = []

        for rental in db_rental_histories:
            # 기자재 정보와 함께 조회
            equipment = rental.equipment

            # 대여 만료일까지 남은 시간 계산
            current_time = datetime.datetime.now()
            time_remaining = rental.due_date - current_time
            days_remaining = time_remaining.days
            hours_remaining = time_remaining.seconds // 3600

            # 만료 상태 확인
            is_overdue = current_time > rental.due_date

            rental_info = {
                "rental_id": rental.id,
                "equipment": {
                    "id": equipment.id,
                    "alias": equipment.alias,
                    "type": (
                        equipment.equipment_type.name
                        if equipment.equipment_type
                        else None
                    ),
                    "status": equipment.status,
                    "status_display": (
                        equipment.equipment_status.display_name
                        if equipment.equipment_status
                        else None
                    ),
                    "comment": equipment.info_comment,
                },
                "rental_date": rental.rental_date.isoformat(),
                "due_date": rental.due_date.isoformat(),
                "days_remaining": days_remaining,
                "hours_remaining": hours_remaining,
                "is_overdue": is_overdue,
                "time_status": (
                    "overdue"
                    if is_overdue
                    else ("expiring_soon" if days_remaining <= 1 else "normal")
                ),
            }

            rentals_list.append(rental_info)

        # 만료일 순으로 정렬 (오버듀 먼저, 그 다음 만료일 임박)
        rentals_list.sort(key=lambda x: (x["is_overdue"], x["due_date"]), reverse=True)

        return {
            "message": f"현재 대여 중인 기자재 {len(rentals_list)}개를 조회했습니다",
            "rentals": rentals_list,
            "total_count": len(rentals_list),
            "overdue_count": len([r for r in rentals_list if r["is_overdue"]]),
            "expiring_soon_count": len(
                [
                    r
                    for r in rentals_list
                    if r["days_remaining"] <= 1 and not r["is_overdue"]
                ]
            ),
        }

    @staticmethod
    @get_execution_time_decorator
    async def get_rental_history(session: AsyncSession, user_id: str, limit: int = 50) -> dict:
        """
        사용자의 대여 이력을 조회합니다.

        Args:
            session: 데이터베이스 세션
            user_id: 사용자 아이디
            limit: 조회할 최대 개수

        Returns:
            dict: 대여 이력 목록
        """
        # 사용자의 모든 대여 이력 조회 (최신순)
        rental_query = select(RentalHistory).where(
            RentalHistory.user_id == user_id
        ).order_by(RentalHistory.rental_date.desc()).limit(limit)
        rental_result = await session.execute(rental_query)
        db_rental_histories = rental_result.scalars().all()

        if not db_rental_histories:
            return {
                "message": "대여 이력이 없습니다",
                "rental_history": [],
                "total_count": 0,
            }

        history_list = []

        for rental in db_rental_histories:
            # 기자재 정보와 함께 조회
            equipment = rental.equipment

            history_info = {
                "rental_id": rental.id,
                "equipment": {
                    "id": equipment.id,
                    "alias": equipment.alias,
                    "type": (
                        equipment.equipment_type.name
                        if equipment.equipment_type
                        else None
                    ),
                    "status": equipment.status,
                    "status_display": (
                        equipment.equipment_status.display_name
                        if equipment.equipment_status
                        else None
                    ),
                    "comment": equipment.info_comment,
                },
                "rental_date": rental.rental_date.isoformat(),
                "due_date": rental.due_date.isoformat(),
                "return_date": (
                    rental.return_date.isoformat() if rental.return_date else None
                ),
                "is_returned": rental.is_returned,
                "rental_duration": (
                    (rental.return_date - rental.rental_date).days
                    if rental.return_date
                    else None
                ),
            }

            history_list.append(history_info)

        return {
            "message": f"대여 이력 {len(history_list)}개를 조회했습니다",
            "rental_history": history_list,
            "total_count": len(history_list),
        }

    @staticmethod
    @get_execution_time_decorator
    async def extend_rental_period(rental_id: str, new_due_date: datetime, session: AsyncSession, user_id: str) -> dict:
        """
        대여 기간을 연장합니다.
        
        Args:
            rental_id: 대여 이력 ID
            new_due_date: 새로운 만료일
            session: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            dict: 연장 결과 정보
            
        Raises:
            ValueError: 대여를 찾을 수 없거나 권한이 없거나 이미 반납된 경우
        """
        from datetime import datetime
        from sqlalchemy import select
        from app.models.rental_history import RentalHistory
        
        # 현재 시간
        current_time = datetime.now()
        
        # 대여 이력 조회 및 검증
        rental_query = select(RentalHistory).where(
            RentalHistory.id == rental_id,
            RentalHistory.user_id == user_id,
            RentalHistory.is_returned == False  # 반납되지 않은 대여만
        )
        rental_result = await session.execute(rental_query)
        rental = rental_result.scalar_one_or_none()
        
        if not rental:
            raise ValueError("해당 대여를 찾을 수 없거나 연장할 수 없습니다")
        
        # 새로운 만료일 검증
        if new_due_date <= rental.due_date:
            raise ValueError("새로운 만료일은 현재 만료일보다 이후여야 합니다")
        
        if new_due_date <= current_time:
            raise ValueError("새로운 만료일은 현재 시간보다 이후여야 합니다")
        
        # 대여 기간 연장 (최대 30일까지)
        max_extension_days = 30
        original_rental_duration = (rental.due_date - rental.rental_date).days
        new_rental_duration = (new_due_date - rental.rental_date).days
        
        if new_rental_duration - original_rental_duration > max_extension_days:
            raise ValueError(f"대여 기간은 최대 {max_extension_days}일까지만 연장할 수 있습니다")
        
        # 원래 만료일 저장
        original_due_date = rental.due_date
        
        # 만료일 업데이트
        rental.due_date = new_due_date
        rental.updated_at = current_time
        
        await session.commit()
        await session.refresh(rental)
        
        # 연장된 기간 계산
        extended_days = (new_due_date - original_due_date).days
        
        return {
            "message": f"대여 기간이 {extended_days}일 연장되었습니다",
            "rental_id": rental.id,
            "equipment_id": rental.equipment_id,
            "original_due_date": original_due_date.isoformat(),
            "new_due_date": new_due_date.isoformat(),
            "extended_days": extended_days,
            "is_extended": True
        }

    @staticmethod
    @get_execution_time_decorator
    async def get_rental_detail(rental_id: str, session: AsyncSession, user_id: str) -> dict:
        """
        특정 대여의 상세 정보를 조회합니다.
        
        Args:
            rental_id: 대여 이력 ID
            session: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            dict: 대여 상세 정보
            
        Raises:
            ValueError: 대여를 찾을 수 없거나 권한이 없는 경우
        """
        from datetime import datetime, timedelta
        from sqlalchemy import select
        from app.models.rental_history import RentalHistory
        from app.models.equipment import Equipment
        
        # 대여 이력 조회 (사용자 권한 확인)
        rental_query = select(RentalHistory).where(
            RentalHistory.id == rental_id,
            RentalHistory.user_id == user_id
        )
        rental_result = await session.execute(rental_query)
        rental = rental_result.scalar_one_or_none()
        
        if not rental:
            raise ValueError("해당 대여를 찾을 수 없거나 접근 권한이 없습니다")
        
        # 기자재 정보 조회
        equipment_query = select(Equipment).where(Equipment.id == rental.equipment_id)
        equipment_result = await session.execute(equipment_query)
        equipment = equipment_result.scalar_one_or_none()
        
        if not equipment:
            raise ValueError("대여된 기자재 정보를 찾을 수 없습니다")
        
        # 현재 시간
        current_time = datetime.now()
        
        # 시간 상태 계산
        time_status = "normal"
        is_overdue = False
        days_remaining = None
        hours_remaining = None
        can_extend = False
        
        if rental.is_returned:
            time_status = "returned"
            rental_duration = (rental.return_date - rental.rental_date).days if rental.return_date else None
        else:
            # 반납되지 않은 경우
            rental_duration = (current_time - rental.rental_date).days
            
            # 남은 시간 계산
            time_diff = rental.due_date - current_time
            
            if time_diff.total_seconds() <= 0:
                # 오버듀
                time_status = "overdue"
                is_overdue = True
                days_remaining = 0
                hours_remaining = 0
            else:
                # 남은 시간이 있는 경우
                days_remaining = time_diff.days
                hours_remaining = int(time_diff.total_seconds() / 3600)
                
                # 만료 임박 체크 (24시간 이내)
                if time_diff <= timedelta(hours=24):
                    time_status = "expiring_soon"
                else:
                    time_status = "normal"
                
                # 연장 가능 여부 체크 (최대 30일 연장 가능)
                max_extension_days = 30
                original_rental_duration = (rental.due_date - rental.rental_date).days
                if original_rental_duration < max_extension_days:
                    can_extend = True
        
        # 기자재 정보 구성
        equipment_info = {
            "id": equipment.id,
            "alias": equipment.alias,
            "type": (
                equipment.equipment_type.name
                if equipment.equipment_type
                else None
            ),
            "status": equipment.status,
            "status_display": (
                equipment.equipment_status.display_name
                if equipment.equipment_status
                else None
            ),
            "comment": equipment.info_comment,
        }
        
        # 대여 상세 정보 구성
        rental_detail = {
            "rental_id": rental.id,
            "equipment": equipment_info,
            "rental_date": rental.rental_date.isoformat(),
            "due_date": rental.due_date.isoformat(),
            "return_date": (
                rental.return_date.isoformat() if rental.return_date else None
            ),
            "is_returned": rental.is_returned,
            "rental_duration": rental_duration,
            "days_remaining": days_remaining,
            "hours_remaining": hours_remaining,
            "is_overdue": is_overdue,
            "time_status": time_status,
            "can_extend": can_extend,
        }
        
        return {
            "message": "대여 상세 정보를 조회했습니다",
            "rental_detail": rental_detail,
        }
