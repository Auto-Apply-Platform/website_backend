from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from fastapi import HTTPException

from app.repositories.audit_event import AuditEventRepository
from app.repositories.response import ResponseRepository
from app.schemas.response import (
    ResponseCreatePayload,
    ResponseDetailResponse,
    ResponseInDB,
)
from app.schemas.response_stage import ResponseStage
from app.utils.mongo import serialize_document


async def create_response(
    db: AsyncIOMotorDatabase,
    *,
    payload: ResponseCreatePayload,
) -> ResponseInDB:
    repo = ResponseRepository(db)
    audit_repo = AuditEventRepository(db)
    now = datetime.now(timezone.utc)

    try:
        request_object_id = ObjectId(payload.request_id)
        developer_object_id = ObjectId(payload.developer_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заявка или разработчик не найдены")

    request = await db["requests"].find_one({"_id": request_object_id})
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    developer = await db["developers"].find_one({"_id": developer_object_id})
    if not developer:
        raise HTTPException(status_code=404, detail="Разработчик не найден")

    existing = await repo.get_by_request_developer(
        payload.request_id,
        payload.developer_id,
    )
    if existing:
        raise HTTPException(status_code=409, detail="Отклик уже существует")

    response_payload = {
        "request_id": payload.request_id,
        "developer_id": payload.developer_id,
        "rate": payload.rate,
        "stage": ResponseStage.NEW.value,
        "created_at": now,
        "updated_at": now,
    }
    try:
        created = await repo.create(response_payload)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Отклик уже существует")

    response_id = created.get("id") or ""
    await audit_repo.create(
        {
            "entity_type": "response",
            "entity_id": response_id,
            "action": "response_created",
            "payload_json": {
                "request_id": payload.request_id,
                "developer_id": payload.developer_id,
                "rate": payload.rate,
                "stage": ResponseStage.NEW.value,
            },
            "created_at": now,
        }
    )

    return ResponseInDB.model_validate(created)


async def update_response(
    db: AsyncIOMotorDatabase,
    *,
    response_id: str,
    stage: ResponseStage | None,
    rate: str | None,
) -> ResponseInDB:
    repo = ResponseRepository(db)
    audit_repo = AuditEventRepository(db)
    now = datetime.now(timezone.utc)

    response = await repo.get_by_id(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    update_payload: dict[str, object] = {"updated_at": now}
    current_stage_raw = response.get("stage")
    current_stage = (
        ResponseStage(current_stage_raw) if isinstance(current_stage_raw, str) else None
    )
    current_rate = response.get("rate")

    if stage is not None:
        update_payload["stage"] = stage.value
    if rate is not None:
        update_payload["rate"] = rate

    updated = await repo.update_by_id(response_id, update_payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    if stage is not None:
        await audit_repo.create(
            {
                "entity_type": "response",
                "entity_id": response_id,
                "action": "response_stage_changed",
                "payload_json": {
                    "from": current_stage.value if current_stage else None,
                    "to": stage.value,
                },
                "created_at": now,
            }
        )
    if rate is not None:
        await audit_repo.create(
            {
                "entity_type": "response",
                "entity_id": response_id,
                "action": "response_rate_changed",
                "payload_json": {
                    "from": current_rate,
                    "to": rate,
                },
                "created_at": now,
            }
        )

    return ResponseInDB.model_validate(updated)


async def delete_response(
    db: AsyncIOMotorDatabase,
    *,
    response_id: str,
) -> None:
    repo = ResponseRepository(db)
    audit_repo = AuditEventRepository(db)
    now = datetime.now(timezone.utc)

    response = await repo.get_by_id(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")
    deleted = await repo.delete_by_id(response_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Отклик не найден")
    await audit_repo.create(
        {
            "entity_type": "response",
            "entity_id": response_id,
            "action": "response_deleted",
            "payload_json": {
                "request_id": response.get("request_id"),
                "developer_id": response.get("developer_id"),
                "stage": response.get("stage"),
            },
            "created_at": now,
        }
    )


async def get_response_detail(
    db: AsyncIOMotorDatabase,
    *,
    response_id: str,
) -> ResponseDetailResponse:
    repo = ResponseRepository(db)
    response = await repo.get_by_id(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    request_id = response.get("request_id") or ""
    developer_id = response.get("developer_id") or ""
    request = None
    developer = None
    try:
        request = await db["requests"].find_one({"_id": ObjectId(request_id)})
    except Exception:
        request = None
    try:
        developer = await db["developers"].find_one({"_id": ObjectId(developer_id)})
    except Exception:
        developer = None
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if not developer:
        raise HTTPException(status_code=404, detail="Разработчик не найден")

    candidate = await db["candidates"].find_one(
        {"request_id": request_id, "developer_id": developer_id}
    )

    response_model = ResponseInDB.model_validate(serialize_document(response))
    return ResponseDetailResponse(
        response=response_model,
        developer={
            "id": developer_id,
            "full_name": developer.get("full_name") or "",
        },
        request={
            "id": request_id,
            "name": request.get("name"),
            "raw_text": request.get("raw_text"),
            "vacancy": request.get("vacancy"),
            "meta": request.get("meta"),
        },
        candidate=(
            {
                "score": candidate.get("score"),
                "description": candidate.get("description"),
            }
            if candidate
            else None
        ),
    )
