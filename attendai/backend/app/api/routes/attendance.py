"""Attendance API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.api.routes.auth import get_current_user
from app.models import AttendanceRecord

router = APIRouter()

@router.get("", summary="Get attendance records")
async def get_records(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user)
):
    result = await db.execute(
        select(AttendanceRecord).order_by(desc(AttendanceRecord.detected_at)).limit(limit)
    )
    records = result.scalars().all()
    return {"items": [{"id": str(r.id), "person_id": str(r.person_id),
                       "status": r.status.value, "confidence": r.confidence,
                       "detected_at": r.detected_at.isoformat()} for r in records]}
