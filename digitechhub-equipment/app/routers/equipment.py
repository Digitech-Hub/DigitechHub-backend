"""
Equipment 라우터

장비 관련 API 엔드포인트들을 정의합니다.
"""


from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.equipments.interface import \
    EquipmentManagementServiceInterface
from app.utils import ResponseFactory, logger
from app.utils.dependencies import get_database, get_equipment_service

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
async def health_check(
    session: AsyncSession = Depends(get_database),
):
    """
    서비스 상태 확인 엔드포인트

    데이터베이스 연결을 테스트하여 서비스의 가용성을 확인합니다.
    이 엔드포인트는 인증이 필요하지 않으며, 모니터링 시스템에서 사용할 수 있습니다.
    """
    try:
        logger.info("Database health check requested")
        result = await session.execute(select(1))

        if result and result.scalar_one() == 1:
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
    query: str = Query(
        "", description="검색어 (기자재 별칭 또는 설명에서 검색)", example="MacBook"
    ),
    category: str = Query(
        "", description="기자재 카테고리 필터", example="노트북"
    ),
    offset: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_database),
    equipment_service: EquipmentManagementServiceInterface = Depends(
        get_equipment_service
    ),
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
        equipment_list = await equipment_service.get_public_equipment_list(
            session, query=query, category=category, offset=offset, limit=limit
        )

        logger.info(f"Retrieved {equipment_list.total} public equipments successfully")
        return ResponseFactory.success(
            message="기자재 목록",
            data=equipment_list
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
    equipment_service: EquipmentManagementServiceInterface = Depends(
        get_equipment_service
    ),
):
    """
    기자재 아이디로 기자재 조회

    - **equipment_id**: 조회할 기자재의 고유 ID
    - **is_public**: True인 기자재만 조회 가능
    - **인증**: 불필요
    """
    try:
        logger.info(f"Getting public equipment by equipment id={equipment_id}")

        equipment = await equipment_service.get_public_equipment(
            session, equipment_id=equipment_id
        )
        logger.info("Retrieved public equipment successfully")
        return ResponseFactory.success(message="기자재", data={"equipment": equipment})
    except Exception as e:
        logger.error(f"Failed to get equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve equipments: {str(e)}"
        )
