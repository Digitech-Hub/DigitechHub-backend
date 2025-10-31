from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rental_histories.interface import \
    RentalHistoryServiceInterface
from app.utils import logger
from app.utils.dependencies import (get_current_user, get_database,
                                    get_rental_history_service)
from app.utils.response_factory import ResponseFactory

router = APIRouter(
    prefix="/api/equipments/rental-history",
    tags=["Rental History"],
    responses={
        401: {"description": "Unauthorized - JWT token required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get(
    "/",
    summary="현재 대여 중인 기자재 목록",
    description="현재 사용자가 대여 중인 기자재 목록을 조회합니다. 오버듀 상태와 만료 임박 상태를 포함합니다.",
    response_description="대여 중인 기자재 목록",
    responses={
        200: {
            "description": "대여 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "현재 대여 중인 기자재 2개를 조회했습니다",
                        "data": {
                            "message": "현재 대여 중인 기자재 2개를 조회했습니다",
                            "rentals": [
                                {
                                    "rental_id": "rental_123",
                                    "equipment": {
                                        "id": "equipment_456",
                                        "alias": "MacBook Pro",
                                        "type": "노트북",
                                        "status": "rented",
                                        "status_display": "대여 중",
                                        "comment": "조심히 사용하세요",
                                    },
                                    "rental_date": "2024-01-01T10:00:00",
                                    "due_date": "2024-01-15T18:00:00",
                                    "days_remaining": 3,
                                    "hours_remaining": 12,
                                    "is_overdue": False,
                                    "time_status": "normal",
                                }
                            ],
                            "total_count": 2,
                            "overdue_count": 0,
                            "expiring_soon_count": 1,
                        },
                        "error": None,
                    }
                }
            },
        },
        401: {
            "description": "인증 필요",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Authentication required",
                        "data": None,
                        "error": "JWT token missing or invalid",
                    }
                }
            },
        },
    },
)
async def get_rental_status(
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    rental_history_service: RentalHistoryServiceInterface = Depends(
        get_rental_history_service
    ),
    start_date_range: datetime | None = None,
    end_date_range: datetime | None = None,
    equipment_id: str | None = None,
    include_returned: bool = False,
    offset: int = 0,
    limit: int = 10,
    search: str = "",
):
    """
    사용자의 현재 대여 중 기자재 목록 조회

    - **인증**: JWT 토큰 필요
    - **반환 정보**: 대여 중인 기자재 목록, 시간 상태, 통계 정보
    - **정렬**: 오버듀 → 만료 임박 → 정상 순
    """
    try:
        logger.info(
            f"User {current_user['username']} (ID: {current_user['userId']}) requesting to get rented equipment list"
        )

        result = await rental_history_service.get_user_rentals(
            session,
            user_id=current_user["userId"],
            start_date_range=start_date_range,
            end_date_range=end_date_range,
            equipment_id=equipment_id,
            include_returned=include_returned,
            offset=offset,
            limit=limit,
            search=search,
        )

        return ResponseFactory.success(
            message="대여 중인 기자재 목록을 조회했습니다.", data=result
        )
    except Exception as e:
        logger.error(f"Failed to get rented equipment list: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get rented equipment list: {str(e)}"
        )


@router.get(
    "/{rental_id}",
    summary="대여 내역 상세 조회",
    description="특정 대여의 상세 정보를 조회합니다. 본인의 대여만 조회 가능합니다.",
    response_description="대여 상세 정보",
    responses={
        200: {
            "description": "대여 상세 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "대여 상세 정보를 조회했습니다",
                        "data": {
                            "message": "대여 상세 정보를 조회했습니다",
                            "rental_detail": {
                                "rental_id": "rental_123",
                                "equipment": {
                                    "id": "equipment_456",
                                    "alias": "MacBook Pro",
                                    "type": "노트북",
                                    "status": "rented",
                                    "status_display": "대여 중",
                                    "comment": "조심히 사용하세요",
                                },
                                "rental_date": "2024-01-01T10:00:00",
                                "due_date": "2024-01-15T18:00:00",
                                "return_date": None,
                                "is_returned": False,
                                "rental_duration": 5,
                                "days_remaining": 9,
                                "hours_remaining": 32,
                                "is_overdue": False,
                                "time_status": "normal",
                                "can_extend": True,
                            },
                        },
                        "error": None,
                    }
                }
            },
        },
        401: {
            "description": "인증 필요",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Authentication required",
                        "data": None,
                        "error": "JWT token missing or invalid",
                    }
                }
            },
        },
        404: {
            "description": "대여를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "해당 대여를 찾을 수 없거나 접근 권한이 없습니다",
                        "data": None,
                        "error": "Rental not found",
                    }
                }
            },
        },
    },
)
async def get_rental_detail(
    rental_id: str = Path(..., description="대여 이력 ID", example="rental_123"),
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    rental_history_service: RentalHistoryServiceInterface = Depends(
        get_rental_history_service
    ),
):
    """
    특정 대여의 상세 정보 조회

    - **rental_id**: 조회할 대여 이력의 ID
    - **인증**: JWT 토큰 필요
    - **권한**: 본인의 대여만 조회 가능
    - **포함 정보**: 기자재 정보, 대여 기간, 남은 시간, 연장 가능 여부 등
    """
    try:
        logger.info(
            f"User {current_user['username']} (ID: {current_user['userId']}) requesting rental detail for {rental_id}"
        )

        result = await rental_history_service.get_rental_info(
            session, rental_id=rental_id, user_id=current_user["userId"]
        )

        logger.info(
            f"Rental detail {rental_id} successfully retrieved by user {current_user['username']}"
        )

        return ResponseFactory.success(
            message="기자재 대여 이력을 조회했습니다.", data=result
        )

    except ValueError as e:
        logger.warning(f"Invalid rental detail request: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to get rental detail: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get rental detail: {str(e)}"
        )
