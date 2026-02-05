from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from bson import ObjectId
from redis.asyncio import Redis

from app.repositories.developer import DeveloperRepository
from app.repositories.audit_event import AuditEventRepository
from app.schemas.developer import (
    DeveloperInDB,
    DeveloperListItem,
    DeveloperListResponse,
    DeveloperPatchPayload,
    DeveloperUploadResponse,
)
from app.services.roles import role_exists
from app.utils.files import (
    FileTooLargeError,
    MissingFileError,
    UnsupportedFileTypeError,
    UploadValidationError,
    delete_upload,
    save_upload,
)
from app.core.config import settings
from app.services.resume_parser import determine_parsing_status

QUEUE_RESUME_INGEST = "queue:resume_ingest"
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def list_developers(
    db: AsyncIOMotorDatabase,
    *,
    page: int,
    size: int,
    offset: int | None,
    q: str | None,
    role: str | None,
    grade: str | None,
    work_format: str | None,
) -> DeveloperListResponse:
    repo = DeveloperRepository(db)
    skip = offset if offset is not None else (page - 1) * size
    filters: dict[str, object] = {}
    if q:
        filters["full_name"] = {"$regex": q, "$options": "i"}
    if role:
        filters["role"] = role
    if grade:
        filters["grade"] = grade
    if work_format:
        filters["work_format"] = work_format
    developers = await repo.list(
        skip=skip,
        limit=size,
        sort=[("created_at", -1)],
        filters=filters,
    )
    items: list[DeveloperListItem] = []
    for developer in developers:
        stack = developer.get("stack") or {}
        created_at = developer.get("created_at") or ""
        experience = developer.get("experience_years")
        experience_value = (
            float(experience) if isinstance(experience, (int, float)) else 0.0
        )
        full_name = developer.get("full_name") or ""
        role_value = developer.get("role") or ""
        status_value = developer.get("status")
        rate_value = developer.get("rate")
        grade_value = developer.get("grade")
        work_format_value = developer.get("work_format")
        parsing_status = developer.get("parsing_status") or ""
        items.append(
            DeveloperListItem(
                id=developer.get("id") or "",
                full_name=full_name,
                role=role_value,
                status=status_value,
                rate=rate_value,
                stack={
                    "core": stack.get("core") or [],
                    "additional": stack.get("additional") or [],
                },
                experience=experience_value,
                parsing_status=parsing_status,
                created_at=created_at,
                grade=grade_value or "",
                work_format=work_format_value or "",
            )
        )
    total = await repo.count(filters=filters)
    return DeveloperListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


async def get_developer_by_id(
    db: AsyncIOMotorDatabase,
    *,
    developer_id: str,
) -> DeveloperInDB:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")
    repo = DeveloperRepository(db)
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(status_code=404, detail="Разработчик не найден")
    return DeveloperInDB.model_validate(developer)


async def create_developer(
    db: AsyncIOMotorDatabase,
    *,
    resume: list[UploadFile],
) -> DeveloperUploadResponse:
    if len(resume) != 1:
        raise HTTPException(
            status_code=422,
            detail="Разрешен только один файл резюме",
        )
    try:
        resume_path, saved_path = await save_upload(
            resume[0],
            settings.uploads_dir,
            max_size_bytes=MAX_RESUME_SIZE_BYTES,
            allowed_extensions=ALLOWED_EXTENSIONS,
            allowed_content_types=ALLOWED_CONTENT_TYPES,
        )
    except MissingFileError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except UploadValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    created_at = datetime.now(timezone.utc)
    payload = {
        "resume_path": resume_path,
        "parsing_status": "pending",
        "created_at": created_at,
        "updated_at": created_at,
        "status": "доступен",
    }
    repo = DeveloperRepository(db)
    created = await repo.create(payload)
    developer_id = created.get("id")
    if not developer_id:
        raise HTTPException(
            status_code=500,
            detail="Не удалось создать запись резюме",
        )
    task = {
        "task_id": str(uuid.uuid4()),
        "source": "website_upload",
        "file_path": str(saved_path),
        "meta": {
            "developer_id": developer_id,
            "resume_path": resume_path,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.rpush(QUEUE_RESUME_INGEST, json.dumps(task))
    finally:
        await redis.close()
    return DeveloperUploadResponse(
        id=developer_id,
        resume_path=resume_path,
        parsing_status="pending",
    )


async def update_developer(
    db: AsyncIOMotorDatabase,
    *,
    developer_id: str,
    payload: DeveloperPatchPayload,
) -> DeveloperInDB:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")
    repo = DeveloperRepository(db)
    audit_repo = AuditEventRepository(db)
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(status_code=404, detail="Разработчик не найден")
    update_data = payload.model_dump(exclude_unset=True)
    if "grade" in update_data and isinstance(update_data["grade"], str):
        update_data["grade"] = update_data["grade"].strip().lower()
    if "work_format" in update_data and isinstance(update_data["work_format"], str):
        update_data["work_format"] = update_data["work_format"].strip().lower()
    now = datetime.now(timezone.utc)
    update_data["updated_at"] = now
    if "role" in update_data and update_data["role"] is not None:
        role_value = str(update_data["role"])
        exists = await role_exists(db, name=role_value)
        if not exists:
            raise HTTPException(
                status_code=422,
                detail="Роль не найдена в списке доступных",
            )
    merged = {**developer, **update_data}
    parsing_status = await determine_parsing_status(merged)
    update_data["parsing_status"] = parsing_status
    updated = await repo.update_by_id(developer_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Разработчик не найден")
    parsed = DeveloperInDB.model_validate(updated)
    if parsed.parsing_status == "accepted":
        task = {
            "task_id": str(uuid.uuid4()),
            "action": "match_only",
            "meta": {
                "developer_id": developer_id,
            },
            "created_at": now.isoformat(),
        }
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await redis.rpush(QUEUE_RESUME_INGEST, json.dumps(task))
        finally:
            await redis.close()
        await audit_repo.create(
            {
                "entity_type": "developer",
                "entity_id": developer_id,
                "action": "developer_rematch_requested",
                "payload_json": {
                    "action": "match_only",
                    "parsing_status": parsed.parsing_status,
                },
                "created_at": now,
            }
        )
    return parsed


async def get_developer_resume(
    db: AsyncIOMotorDatabase,
    *,
    developer_id: str,
) -> FileResponse:
    developer = await get_developer_by_id(db, developer_id=developer_id)
    resume_path = developer.resume_path
    if not resume_path:
        raise HTTPException(
            status_code=404,
            detail="Файл резюме не найден",
        )
    filename = Path(resume_path).name
    file_path = Path(settings.uploads_dir) / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Файл резюме не найден",
        )
    extension = file_path.suffix
    full_name = (developer.full_name or "").strip()
    safe_name = full_name.replace("/", "_").replace("\\", "_") if full_name else "resume"
    download_name = f"{safe_name}{extension}"
    return FileResponse(file_path, filename=download_name)


async def delete_developer(
    db: AsyncIOMotorDatabase,
    *,
    developer_id: str,
) -> None:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")
    repo = DeveloperRepository(db)
    audit_repo = AuditEventRepository(db)
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(status_code=404, detail="Разработчик не найден")
    now = datetime.now(timezone.utc)
    try:
        delete_upload(
            developer.get("resume_path"),
            settings.uploads_dir,
        )
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Не удалось удалить файл резюме",
        ) from exc

    responses_result = await db["responses"].delete_many(
        {"developer_id": developer_id}
    )
    candidates_result = await db["candidates"].delete_many(
        {"developer_id": developer_id}
    )

    deleted = await repo.delete_by_id(developer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Разработчик не найден")

    await audit_repo.create(
        {
            "entity_type": "developer",
            "entity_id": developer_id,
            "action": "developer_deleted",
            "payload_json": {
                "responses_deleted": responses_result.deleted_count,
                "candidates_deleted": candidates_result.deleted_count,
                "resume_path": developer.get("resume_path"),
            },
            "created_at": now,
        }
    )
