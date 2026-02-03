from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.schemas.kanban import KanbanResponse
from app.services.kanban import get_kanban

router = APIRouter(prefix="/kanban", tags=["kanban"])


@router.get("", response_model=KanbanResponse)
async def kanban(
    db: AsyncIOMotorDatabase = Depends(get_db),
    role: str | None = Query(None),
    grade: str | None = Query(None),
    work_format: str | None = Query(None),
    has_deadline: bool | None = Query(None),
) -> KanbanResponse:
    return await get_kanban(
        db,
        role=role,
        grade=grade,
        work_format=work_format,
        has_deadline=has_deadline,
    )
