"""
관리자용 기자재 라우터

관리자 권한의 기자재 관리 API 엔드포인트들을 정의합니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom import BaseAPIException
from app.services.admin.interface import AdminEquipmentServiceInterface
from app.utils import ResponseFactory, logger
from app.utils.dependencies import (get_admin_service, get_database,
                                    require_role)

router = APIRouter(
    prefix="/api/equipments/admin",
    tags=["Admin Equipment Management"],
    responses={
        401: {"description": "Unauthorized - JWT token required"},
        403: {"description": "Forbidden - ADMIN role required"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get(
    "/",
    summary="전체 기자재 목록 조회 (관리자)",
    description="관리자 권한으로 모든 기자재 목록을 조회합니다. 비공개 기자재 포함 가능합니다.",
    response_description="기자재 목록과 총 개수",
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_all_equipments(
    query: str | None = None,
    category: str | None = None,
    status: str | None = None,
    include_private: bool = True,
    offset: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_database),
    admin_service: AdminEquipmentServiceInterface = Depends(get_admin_service),
):
    """
    관리자용 기자재 목록 조회

    - **query**: 검색어 (별칭, 설명, 관리자 코멘트에서 검색)
    - **category**: 기자재 유형으로 필터링
    - **status**: 기자재 상태로 필터링
    - **include_private**: 비공개 기자재 포함 여부 (기본값: True)
    - **인증**: ADMIN 권한 필요
    """
    try:
        logger.info("Admin: Getting all equipment list")

        equipment_list = await admin_service.get_equipment_list(
            session,
            query=query,
            category=category,
            status=status,
            include_private=include_private,
            offset=offset,
            limit=limit,
        )

        logger.info(f"Admin: Retrieved {equipment_list.total} equipments successfully")
        return ResponseFactory.success(message="기자재 목록", data=equipment_list)

    except Exception as e:
        logger.error(f"Failed to get all equipment list: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get all equipment list: {str(e)}"
        )


@router.get(
    "/{equipment_id}",
    summary="기자재 상세 조회 (관리자)",
    description="관리자 권한으로 특정 기자재의 상세 정보를 조회합니다. 비공개 기자재 포함 가능합니다.",
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_equipment_detail(
    equipment_id: str,
    session: AsyncSession = Depends(get_database),
    admin_service: AdminEquipmentServiceInterface = Depends(get_admin_service),
):
    """
    관리자용 기자재 상세 조회

    - **equipment_id**: 조회할 기자재의 고유 ID
    - **인증**: ADMIN 권한 필요
    """
    try:
        logger.info(f"Admin: Getting equipment detail for ID={equipment_id}")

        equipment = await admin_service.get_equipment(
            session, equipment_id=equipment_id
        )
        logger.info("Admin: Retrieved equipment detail successfully")

        return ResponseFactory.success(
            message="기자재 상세 정보", data={"equipment": equipment}
        )

    except BaseAPIException as e:
        logger.error(f"Admin error getting equipment detail: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to get equipment detail: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get equipment detail: {str(e)}"
        )


@router.post(
    "/",
    summary="기자재 생성 (관리자)",
    description="관리자 권한으로 새로운 기자재를 생성합니다.",
    dependencies=[Depends(require_role("ADMIN"))],
)
async def create_equipment(
    equipment_type_id: str,
    equipment_status_id: str,
    alias: str | None = None,
    is_public: bool = True,
    admin_comment: str | None = None,
    info_comment: str | None = None,
    session: AsyncSession = Depends(get_database),
    admin_service: AdminEquipmentServiceInterface = Depends(get_admin_service),
):
    """
    기자재 생성

    - **alias**: 기자재 별칭
    - **equipment_type_id**: 기자재 유형 ID (필수)
    - **equipment_status_id**: 기자재 상태 ID (필수)
    - **is_public**: 공개 여부 (기본값: True)
    - **admin_comment**: 관리자 전용 코멘트
    - **info_comment**: 유의사항 및 정보
    - **인증**: ADMIN 권한 필요
    """
    try:
        logger.info("Admin: Creating new equipment")

        equipment = await admin_service.create_equipment(
            session,
            alias=alias,
            equipment_type_id=equipment_type_id,
            equipment_status_id=equipment_status_id,
            is_public=is_public,
            admin_comment=admin_comment,
            info_comment=info_comment,
        )

        logger.info(f"Admin: Created equipment successfully: {equipment.id}")
        return ResponseFactory.success(
            message="기자재 생성 성공", data={"equipment": equipment}
        )

    except BaseAPIException as e:
        logger.error(f"Admin error creating equipment: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create equipment: {str(e)}"
        )


@router.put(
    "/{equipment_id}",
    summary="기자재 수정 (관리자)",
    description="관리자 권한으로 기자재 정보를 수정합니다.",
    dependencies=[Depends(require_role("ADMIN"))],
)
async def update_equipment(
    equipment_id: str,
    alias: str | None = None,
    equipment_type_id: str | None = None,
    equipment_status_id: str | None = None,
    is_public: bool | None = None,
    admin_comment: str | None = None,
    info_comment: str | None = None,
    session: AsyncSession = Depends(get_database),
    admin_service: AdminEquipmentServiceInterface = Depends(get_admin_service),
):
    """
    기자재 정보 수정

    - **equipment_id**: 수정할 기자재 ID
    - **인증**: ADMIN 권한 필요
    """
    try:
        logger.info(f"Admin: Updating equipment ID={equipment_id}")

        equipment = await admin_service.update_equipment(
            session,
            equipment_id=equipment_id,
            alias=alias,
            equipment_type_id=equipment_type_id,
            equipment_status_id=equipment_status_id,
            is_public=is_public,
            admin_comment=admin_comment,
            info_comment=info_comment,
        )

        logger.info(f"Admin: Updated equipment successfully: {equipment.id}")
        return ResponseFactory.success(
            message="기자재 수정 성공", data={"equipment": equipment}
        )

    except BaseAPIException as e:
        logger.error(f"Admin error updating equipment: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to update equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update equipment: {str(e)}"
        )


@router.delete(
    "/{equipment_id}",
    summary="기자재 삭제 (관리자)",
    description="관리자 권한으로 기자재를 삭제합니다. 대여 중인 기자재는 삭제할 수 없습니다.",
    dependencies=[Depends(require_role("ADMIN"))],
)
async def delete_equipment(
    equipment_id: str,
    session: AsyncSession = Depends(get_database),
    admin_service: AdminEquipmentServiceInterface = Depends(get_admin_service),
):
    """
    기자재 삭제

    - **equipment_id**: 삭제할 기자재 ID
    - **인증**: ADMIN 권한 필요
    - **제약**: 대여 중인 기자재는 삭제 불가
    """
    try:
        logger.info(f"Admin: Deleting equipment ID={equipment_id}")

        await admin_service.delete_equipment(session, equipment_id=equipment_id)

        logger.info(f"Admin: Deleted equipment successfully: {equipment_id}")
        return ResponseFactory.success(message="기자재 삭제 성공")

    except BaseAPIException as e:
        logger.error(f"Admin error deleting equipment: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to delete equipment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete equipment: {str(e)}"
        )
