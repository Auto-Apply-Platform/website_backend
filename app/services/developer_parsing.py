from __future__ import annotations

from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.developer import DeveloperRepository
from app.services.resume_parser import determine_parsing_status, parse_resume_ai


async def run_resume_parsing(
    developer_id: str,
    file_path: Path,
    db: AsyncIOMotorDatabase,
) -> None:
    repo = DeveloperRepository(db)
    try:
        parsed = await parse_resume_ai(str(file_path))
        parsing_status = await determine_parsing_status(parsed)
        update_payload = {**parsed, "parsing_status": parsing_status}
    except Exception:
        update_payload = {"parsing_status": "rejected"}
    await repo.update_by_id(developer_id, update_payload)
