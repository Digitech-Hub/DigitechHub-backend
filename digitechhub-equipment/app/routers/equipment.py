"""
Equipment 라우터

장비 관련 API 엔드포인트들을 정의합니다.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.services import EquipmentService
from app.utils import get_database, ResponseFactory, logger, get_current_user
from app.schemas import RentEquipmentRequest, ExtendRentalRequest

router = APIRouter(
    prefix="/api/equipments",
    tags=["Equipment Management"],
    responses={
        401: {"description": "Unauthorized - JWT token required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get(
    "/health",
    summary="서비스 상태 확인",
    description="데이터베이스 연결 상태와 서비스 가용성을 확인합니다.",
    response_description="서비스 상태 정보",
    responses={
        200: {
            "description": "서비스 정상 작동",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Database connection is healthy",
                        "data": {"status": "OK"},
                        "error": None,
                    }
                }
            },
        },
        500: {
            "description": "데이터베이스 연결 실패",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Database connection failed",
                        "data": None,
                        "error": "Connection timeout",
                    }
                }
            },
        },
    },
)
async def health_check(session: AsyncSession = Depends(get_database)):
    """
    서비스 상태 확인 엔드포인트

    데이터베이스 연결을 테스트하여 서비스의 가용성을 확인합니다.
    이 엔드포인트는 인증이 필요하지 않으며, 모니터링 시스템에서 사용할 수 있습니다.
    """
    try:
        logger.info("Database health check requested")
        result = await EquipmentService.get_database_status(session)

        if result and result[0] == 1:
            logger.info("Database connection successful")
            return ResponseFactory.success(
                message="Database connection is healthy",
                data={
                    "status": "OK",
                },
            )
        else:
            logger.error("Database test query failed")
            raise HTTPException(status_code=500, detail="Database test query failed")

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@router.get(
    "/",
    summary="기자재 목록 조회",
    description="공개된 기자재 목록을 조회합니다. 검색어와 카테고리로 필터링할 수 있습니다.",
    response_description="기자재 목록과 총 개수",
    responses={
        200: {
            "description": "기자재 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "기자재 목록",
                        "data": {
                            "equipments": [
                                {
                                    "id": "equipment_123",
                                    "alias": "MacBook Pro 16",
                                    "type": "노트북",
                                    "status": "available",
                                    "status_display": "사용 가능",
                                    "created_at": "2024-01-01T10:00:00",
                                    "updated_at": "2024-01-01T10:00:00",
                                }
                            ],
                            "total": 1,
                        },
                        "error": None,
                    }
                }
            },
        }
    },
)
async def get_equipments(
    query: Optional[str] = Query(
        None, description="검색어 (기자재 별칭 또는 설명에서 검색)", example="MacBook"
    ),
    category: Optional[str] = Query(
        None, description="기자재 카테고리 필터", example="노트북"
    ),
    session: AsyncSession = Depends(get_database),
):
    """
    공개된 기자재 목록 조회

    - **query**: 기자재 별칭(alias) 또는 설명(info_comment)에서 검색
    - **category**: 기자재 유형으로 필터링
    - **is_public**: True인 기자재들만 반환
    - **인증**: 불필요
    """
    try:
        logger.info("Getting public equipments list")

        # 공개된 기자재 목록 조회
        equipment_list = await EquipmentService.get_public_equipment_list(
            query, category, session
        )

        logger.info(f"Retrieved {len(equipment_list)} public equipments successfully")
        return ResponseFactory.success(
            message="기자재 목록",
            data={"equipments": equipment_list, "total": len(equipment_list)},
        )

    except Exception as e:
        logger.error(f"Failed to get equipments: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve equipments: {str(e)}"
        )


@router.get(
    "/{equipment_id}",
    summary="기자재 상세 정보 조회",
    description="특정 기자재의 상세 정보를 조회합니다. 공개된 기자재만 조회 가능합니다.",
    response_description="기자재 상세 정보",
    responses={
        200: {
            "description": "기자재 정보 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "기자재",
                        "data": {
                            "equipment": {
                                "id": "equipment_123",
                                "alias": "MacBook Pro 16",
                                "type": "노트북",
                                "status": "available",
                                "status_display": "사용 가능",
                                "comment": "조심히 사용하세요",
                                "created_at": "2024-01-01T10:00:00",
                                "updated_at": "2024-01-01T10:00:00",
                            }
                        },
                        "error": None,
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
async def get_equipment_information(
    equipment_id: str = Path(
        ..., description="기자재 고유 ID", example="equipment_123"
    ),
    session: AsyncSession = Depends(get_database),
):
    """
    기자재 아이디로 기자재 조회

    - **equipment_id**: 조회할 기자재의 고유 ID
    - **is_public**: True인 기자재만 조회 가능
    - **인증**: 불필요
    """
    try:
        logger.info(f"Getting public equipment by equipment id={equipment_id}")

        equipment = await EquipmentService.get_public_equipment(equipment_id, session)
        logger.info(f"Retrieved public equipment successfully")
        return ResponseFactory.success(message="기자재", data={"equipment": equipment})
    except Exception as e:
        logger.error(f"Failed to get equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve equipments: {str(e)}"
        )


@router.post(
    "/{equipment_id}/rent",
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

        result = await EquipmentService.rent_equipment(
            equipment_id, rent_equipment_request, current_user["userId"], session
        )

        logger.info(
            f"Equipment {equipment_id} successfully rented to user {current_user['username']}"
        )

        return ResponseFactory.success(
            message=result["message"],
            data=result,
        )

    except Exception as e:
        logger.error(f"Failed to rent equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to rent equipment: {str(e)}"
        )


@router.get(
    "/rentals",
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

        result = await EquipmentService.get_rentals_equipment(session, current_user["userId"])

        return ResponseFactory.success(message=result["message"], data=result)
    except Exception as e:
        logger.error(f"Failed to get rented equipment list: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get rented equipment list: {str(e)}"
        )


@router.get(
    "/rentals/history",
    summary="대여 이력 조회",
    description="사용자의 과거 대여 이력을 조회합니다. 반납 완료된 대여도 포함됩니다.",
    response_description="대여 이력 목록",
    responses={
        200: {
            "description": "대여 이력 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "대여 이력 5개를 조회했습니다",
                        "data": {
                            "message": "대여 이력 5개를 조회했습니다",
                            "rental_history": [
                                {
                                    "rental_id": "rental_123",
                                    "equipment": {
                                        "id": "equipment_456",
                                        "alias": "MacBook Pro",
                                        "type": "노트북",
                                        "status": "available",
                                        "status_display": "사용 가능",
                                        "comment": "조심히 사용하세요",
                                    },
                                    "rental_date": "2024-01-01T10:00:00",
                                    "due_date": "2024-01-15T18:00:00",
                                    "return_date": "2024-01-14T16:30:00",
                                    "is_returned": True,
                                    "rental_duration": 13,
                                }
                            ],
                            "total_count": 5,
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
async def get_rental_history(
    limit: int = Query(
        50, ge=1, le=100, description="조회할 최대 개수 (1-100)", example=50
    ),
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    사용자의 대여 이력 조회

    - **limit**: 조회할 최대 개수 (기본값: 50, 최대: 100)
    - **인증**: JWT 토큰 필요
    - **정렬**: 최신순 (rental_date 기준)
    - **포함**: 반납 완료된 대여도 포함
    """
    try:
        logger.info(
            f"User {current_user['username']} (ID: {current_user['userId']}) requesting rental history"
        )

        result = await EquipmentService.get_rental_history(
            session, current_user["userId"], limit
        )

        return ResponseFactory.success(message=result["message"], data=result)
    except Exception as e:
        logger.error(f"Failed to get rental history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get rental history: {str(e)}"
        )


@router.post(
    "/{rental_id}/extend",
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
    rental_id: str = Path(
        ..., description="대여 이력 ID", example="rental_123"
    ),
    extend_request: ExtendRentalRequest = None,
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
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
        
        result = await EquipmentService.extend_rental_period(
            rental_id, extend_request.new_due_date, session, current_user["userId"]
        )

        logger.info(
            f"Rental {rental_id} successfully extended by user {current_user['username']}"
        )

        return ResponseFactory.success(message=result["message"], data=result)
        
    except ValueError as e:
        logger.warning(f"Invalid extend rental request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Failed to extend rental period: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to extend rental period: {str(e)}"
        )


@router.get(
    "/history/{rental_id}",
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
    rental_id: str = Path(
        ..., description="대여 이력 ID", example="rental_123"
    ),
    session: AsyncSession = Depends(get_database),
    current_user: dict = Depends(get_current_user),
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
        
        result = await EquipmentService.get_rental_detail(
            rental_id, session, current_user["userId"]
        )

        logger.info(
            f"Rental detail {rental_id} successfully retrieved by user {current_user['username']}"
        )

        return ResponseFactory.success(message=result["message"], data=result)
        
    except ValueError as e:
        logger.warning(f"Invalid rental detail request: {e}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        logger.error(f"Failed to get rental detail: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get rental detail: {str(e)}"
        )
