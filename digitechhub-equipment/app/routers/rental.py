from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.input.rental import ExtendRentalRequest, RentEquipmentRequest
from app.services.rental.interface import RentalServiceInterface
from app.utils import logger
from app.utils.dependencies import (get_current_user, get_database,
                                    get_rental_service)
from app.utils.response_factory import ResponseFactory

router = APIRouter(
    prefix="/api/equipments/rental",
    tags=["Equipment Rental"],
    responses={
        401: {"description": "Unauthorized - JWT token required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"},
    },
)


@router.post(
    "/{equipment_id}",
    summary="기자재 대여 요청",
    description="특정 기자재를 대여합니다. 인증된 사용자만 대여 가능하며, 기자재 상태와 중복 대여를 확인합니다.",
    response_description="대여 처리 결과",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "대여 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "기자재 대여가 성공적으로 처리되었습니다",
                        "data": {
                            "rental_history": {
                                "id": "rental_123",
                                "equipment_id": "equipment_456",
                                "user_id": "user_789",
                                "rental_date": "2024-01-01T10:00:00",
                                "due_date": "2024-01-15T18:00:00",
                                "is_returned": False,
                            },
                            "equipment": {
                                "id": "equipment_456",
                                "alias": "MacBook Pro",
                                "status": "rented",
                                "type": "노트북",
                                "status_display": "대여 중",
                            },
                        },
                        "error": None,
                    }
                }
            },
        },
        400: {
            "description": "대여 불가 (이미 대여 중, 사용 불가 상태 등)",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "해당 기자재는 이미 대여 중입니다",
                        "data": None,
                        "error": "Equipment already rented",
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
            "description": "기자재를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "해당하는 기자재를 찾을 수 없습니다",
                        "data": None,
                        "error": "Equipment not found",
                    }
                }
            },
        },
    },
)
async def rent_equipment(
    equipment_id: str,
    rent_equipment_request: RentEquipmentRequest,
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    rental_service: RentalServiceInterface = Depends(get_rental_service),
):
    """
    기자재 대여 요청

    - **equipment_id**: 대여할 기자재의 고유 ID
    - **rent_equipment_request**: 대여 요청 정보 (만료일 포함)
    - **인증**: JWT 토큰 필요
    - **검증**: 기자재 상태, 중복 대여, 만료일 유효성 확인
    """
    try:
        logger.info(
            f"User {current_user['username']} (ID: {current_user['userId']}) requesting to rent equipment {equipment_id}"
        )

        result = await rental_service.rent_equipment(
            session,
            equipment_id=equipment_id,
            user_id=current_user["userId"],
            rent_request=rent_equipment_request,
        )

        logger.info(
            f"Equipment {equipment_id} successfully rented to user {current_user['username']}"
        )

        return ResponseFactory.success(
            message="기자재 대여 접수가 완료되었습니다. 조교실에서 기자재를 수령해주세요.",
            data=result,
        )

    except Exception as e:
        logger.error(f"Failed to rent equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to rent equipment: {str(e)}"
        )


@router.post(
    "/extend/{rental_id}",
    summary="대여 기간 연장",
    description="현재 대여 중인 기자재의 대여 기간을 연장합니다. 최대 30일까지 연장 가능합니다.",
    response_description="대여 연장 처리 결과",
    responses={
        200: {
            "description": "대여 연장 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "대여 기간이 7일 연장되었습니다",
                        "data": {
                            "message": "대여 기간이 7일 연장되었습니다",
                            "rental_id": "rental_123",
                            "equipment_id": "equipment_456",
                            "original_due_date": "2024-01-15T18:00:00",
                            "new_due_date": "2024-01-22T18:00:00",
                            "extended_days": 7,
                            "is_extended": True,
                        },
                        "error": None,
                    }
                }
            },
        },
        400: {
            "description": "연장 불가 (잘못된 날짜, 권한 없음 등)",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "새로운 만료일은 현재 만료일보다 이후여야 합니다",
                        "data": None,
                        "error": "Invalid new due date",
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
                        "message": "해당 대여를 찾을 수 없거나 연장할 수 없습니다",
                        "data": None,
                        "error": "Rental not found",
                    }
                }
            },
        },
    },
)
async def extend_rental_period(
    extend_request: ExtendRentalRequest,
    rental_id: str = Path(..., description="대여 이력 ID", example="rental_123"),
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    rental_service: RentalServiceInterface = Depends(get_rental_service),
):
    """
    대여 기간 연장 요청

    - **rental_id**: 연장할 대여 이력의 ID
    - **extend_request**: 연장 요청 정보 (새로운 만료일 포함)
    - **인증**: JWT 토큰 필요
    - **검증**: 대여 소유권, 새로운 만료일 유효성, 연장 제한 확인
    """
    try:
        logger.info(
            f"User {current_user['username']} (ID: {current_user['userId']}) requesting to extend rental {rental_id}"
        )

        result = await rental_service.extend_rental_period(
            session,
            rental_id=rental_id,
            user_id=current_user["userId"],
            new_due_date=extend_request.new_due_date,
        )

        logger.info(
            f"Rental {rental_id} successfully extended by user {current_user['username']}"
        )

        return ResponseFactory.success(message="대여 기간을 연장했습니다.", data=result)

    except ValueError as e:
        logger.warning(f"Invalid extend rental request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to extend rental period: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to extend rental period: {str(e)}"
        )
