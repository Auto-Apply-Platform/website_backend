from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.services.requests import list_requests as list_requests_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[dict])
async def list_requests(
    db: AsyncIOMotorDatabase = Depends(get_db),
    role: str | None = Query(None),
    grade: str | None = Query(None),
    has_deadline: bool | None = Query(None),
) -> list[dict]:
    return await list_requests_service(
        db,
        role=role,
        grade=grade,
        has_deadline=has_deadline,
    )
