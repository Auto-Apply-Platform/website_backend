from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.services.requests import list_requests as list_requests_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[dict])
async def list_requests(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[dict]:
    return await list_requests_service(db)
