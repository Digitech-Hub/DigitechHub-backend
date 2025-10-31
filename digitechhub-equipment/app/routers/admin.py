from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import get_database, logger
from app.utils.dependencies import require_role

router = APIRouter(
    prefix="/api/admin/equipments",
    tags=["Admin Equipment Management"]
)

@router.get("/", dependencies=[Depends(require_role("ADMIN"))])
async def get_all_equipments(
    session : AsyncSession = Depends(get_database)
):
    try:
        pass
    except Exception as e:
        logger.error(f"Failed to get all equipment list: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get all equipment list: {str(e)}"
        )
