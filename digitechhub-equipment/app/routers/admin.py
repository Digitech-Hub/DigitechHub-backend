from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import get_database, get_current_user, logger

router = APIRouter(
    prefix="/api/admin/equipments",
    tags=["Admin Equipment Management"]
)

@router.get("/")
async def get_all_equipments(
    session : AsyncSession = Depends(get_database),
    current_user : dict = Depends(get_current_user)
):
    try:
        pass
    except Exception as e:
        logger.error(f"Failed to get all equipment list: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get all equipment list: {str(e)}"
        )
