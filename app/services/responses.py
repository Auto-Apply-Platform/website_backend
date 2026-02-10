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
from app.utils.response_stage import STAGE_INDEX, STAGE_ORDER, allowed_stages, can_transition
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
    if developer.get("status") == "занят":
        raise HTTPException(status_code=422, detail="Разработчик занят")

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
        "stage": ResponseStage.CV_SELECTED.value,
        "max_stage": STAGE_INDEX[ResponseStage.CV_SELECTED],
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
                "stage": ResponseStage.CV_SELECTED.value,
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

    if not ObjectId.is_valid(response_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")

    response = await repo.get_by_id(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    update_payload: dict[str, object] = {"updated_at": now}
    current_stage_raw = response.get("stage")
    if isinstance(current_stage_raw, str):
        try:
            current_stage = ResponseStage(current_stage_raw)
        except ValueError:
            current_stage = ResponseStage.CV_SELECTED
    else:
        current_stage = None
    current_rate = response.get("rate")
    current_max_stage = response.get("max_stage")
    max_stage_value = int(current_max_stage) if isinstance(current_max_stage, int) else 1

    stage_order = STAGE_ORDER
    stage_index = STAGE_INDEX

    if stage is not None:
        can_move, next_max_stage = can_transition(
            current_stage,
            stage,
            max_stage_value,
        )
        if not can_move:
            raise HTTPException(status_code=409, detail="Недопустимый переход стадии")
        update_payload["stage"] = stage.value
        update_payload["max_stage"] = next_max_stage
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

    stage_raw = updated.get("stage")
    if isinstance(stage_raw, str):
        try:
            ResponseStage(stage_raw)
        except ValueError:
            updated["stage"] = ResponseStage.CV_SELECTED.value
    response_model = ResponseInDB.model_validate(updated)
    allowed = allowed_stages(
        ResponseStage(response_model.stage) if response_model.stage else None,
        response_model.max_stage or max_stage_value,
    )
    return {**response_model.model_dump(), "allowed_stages": allowed}


async def delete_response(
    db: AsyncIOMotorDatabase,
    *,
    response_id: str,
) -> None:
    repo = ResponseRepository(db)
    audit_repo = AuditEventRepository(db)
    now = datetime.now(timezone.utc)

    if not ObjectId.is_valid(response_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")

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
    if not ObjectId.is_valid(response_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")
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

    response_doc = serialize_document(response)
    stage_raw = response_doc.get("stage")
    if isinstance(stage_raw, str):
        try:
            ResponseStage(stage_raw)
        except ValueError:
            response_doc["stage"] = ResponseStage.CV_SENT.value
    response_model = ResponseInDB.model_validate(response_doc)
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
