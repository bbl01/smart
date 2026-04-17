"""Camera management API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.api.routes.auth import get_current_user
from app.models import Camera

router = APIRouter()

@router.get("", summary="List cameras")
async def list_cameras(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Camera).where(Camera.is_active == True))
    cameras = result.scalars().all()
    return [{"id": str(c.id), "name": c.name, "location": c.location,
             "status": c.status.value, "resolution": c.resolution, "fps": c.fps}
            for c in cameras]
