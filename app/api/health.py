from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, object]:
    db_stats = await db.command("dbstats")
    return {"status": "ok", "db_stats": db_stats}
