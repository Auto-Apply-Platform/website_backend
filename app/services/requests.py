from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.request import RequestRepository
from app.repositories.audit_event import AuditEventRepository
from app.schemas.request import (
    RequestDeleteResponse,
    RequestDetailResponse,
    RequestInDB,
)
from app.schemas.response_stage import ResponseStage
from app.utils.mongo import serialize_document


async def list_requests(
    db: AsyncIOMotorDatabase,
    *,
    role: str | None = None,
    grade: str | None = None,
    work_format: str | None = None,
    has_deadline: bool | None = None,
) -> list[RequestInDB]:
    repo = RequestRepository(db)
    filters: dict[str, object] = {}
    if role:
        filters["vacancy.role"] = role
    if grade:
        filters["vacancy.grade"] = grade
    if work_format:
        filters["vacancy.work_format"] = work_format
    if has_deadline is True:
        filters["vacancy.application_deadline"] = {"$exists": True, "$ne": ""}
    elif has_deadline is False:
        filters["$or"] = [
            {"vacancy.application_deadline": {"$exists": False}},
            {"vacancy.application_deadline": ""},
            {"vacancy.application_deadline": None},
        ]

    docs = await repo.list_requests(filters=filters, sort=[("created_at", -1)])
    return [RequestInDB.model_validate(serialize_document(doc)) for doc in docs]


async def get_request_by_id(
    db: AsyncIOMotorDatabase,
    *,
    request_id: str,
) -> RequestDetailResponse:
    repo = RequestRepository(db)
    request = await repo.get_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    request_model = RequestInDB.model_validate(serialize_document(request))

    candidates_cursor = db["candidates"].find({"request_id": request_id}).sort("score", -1)
    candidate_docs = [serialize_document(doc) async for doc in candidates_cursor]
    candidate_developer_ids = {
        doc.get("developer_id") for doc in candidate_docs if isinstance(doc.get("developer_id"), str)
    }
    developer_object_ids = []
    for developer_id in candidate_developer_ids:
        try:
            developer_object_ids.append(ObjectId(developer_id))
        except Exception:
            continue
    developers_by_id: dict[str, dict] = {}
    if developer_object_ids:
        developer_cursor = db["developers"].find({"_id": {"$in": developer_object_ids}})
        async for developer in developer_cursor:
            developers_by_id[str(developer.get("_id"))] = developer

    response_cursor = db["responses"].find({"request_id": request_id})
    response_docs = [serialize_document(doc) async for doc in response_cursor]
    assigned_developer_ids = {
        doc.get("developer_id") for doc in response_docs if isinstance(doc.get("developer_id"), str)
    }

    candidates = []
    for candidate in candidate_docs:
        developer_id = candidate.get("developer_id") or ""
        developer = developers_by_id.get(developer_id) or {}
        candidates.append(
            {
                "developer": {
                    "id": developer_id,
                    "full_name": developer.get("full_name") or "",
                    "role": developer.get("role"),
                    "grade": developer.get("grade"),
                    "work_format": developer.get("work_format"),
                },
                "score": candidate.get("score"),
                "description": candidate.get("description"),
                "already_assigned": developer_id in assigned_developer_ids,
            }
        )

    responses = []
    for response in response_docs:
        stage_value = response.get("stage")
        try:
            stage = ResponseStage(stage_value) if stage_value else ResponseStage.NEW
        except ValueError:
            stage = ResponseStage.NEW
        responses.append(
            {
                "id": response.get("id") or "",
                "developer_id": response.get("developer_id") or "",
                "rate": response.get("rate"),
                "stage": stage,
                "created_at": response.get("created_at"),
                "updated_at": response.get("updated_at"),
            }
        )

    return RequestDetailResponse(
        id=request_model.id,
        status=request_model.status,
        name=request_model.name,
        vacancy=request_model.vacancy,
        meta=request_model.meta,
        raw_text=request_model.raw_text,
        created_at=request_model.created_at,
        updated_at=request_model.updated_at,
        candidates=candidates,
        responses=responses,
    )


async def update_request(
    db: AsyncIOMotorDatabase,
    *,
    request_id: str,
    status_value: RequestStatus | None,
    name: str | None,
) -> RequestDetailResponse:
    repo = RequestRepository(db)
    audit_repo = AuditEventRepository(db)
    request = await repo.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    current_status_raw = request.get("status")
    current_status = None
    if isinstance(current_status_raw, str):
        try:
            current_status = RequestStatus(current_status_raw)
        except ValueError:
            current_status = None
    update_payload: dict[str, object] = {}
    if status_value is not None:
        update_payload["status"] = status_value.value
    if name is not None:
        update_payload["name"] = name
    if update_payload:
        update_payload["updated_at"] = datetime.now(timezone.utc)
    updated = await repo.update_by_id(request_id, update_payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if status_value is not None:
        await audit_repo.create(
            {
                "entity_type": "request",
                "entity_id": request_id,
                "action": "request_status_changed",
                "payload_json": {
                    "from": current_status.value if current_status else None,
                    "to": status_value.value,
                },
                "created_at": datetime.now(timezone.utc),
            }
        )
    return await get_request_by_id(db, request_id=request_id)


async def delete_request_by_id(
    db: AsyncIOMotorDatabase,
    *,
    request_id: str,
) -> RequestDeleteResponse:
    repo = RequestRepository(db)
    deleted = await repo.delete_request_by_id(request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return RequestDeleteResponse(id=request_id, deleted=True)
