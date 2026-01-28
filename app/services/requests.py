from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from fastapi import HTTPException, status

from app.repositories.request import RequestRepository
from app.schemas.request import (
    RequestDeleteResponse,
    RequestInDB,
    RequestStatusResponse,
)
from app.schemas.request_status import RequestStatus
from app.services.request_status import can_transition, is_cancel_status, stage
from app.utils.mongo import serialize_document


async def list_requests(
    db: AsyncIOMotorDatabase,
    *,
    role: str | None = None,
    grade: str | None = None,
    has_deadline: bool | None = None,
) -> list[RequestInDB]:
    repo = RequestRepository(db)
    filters: dict[str, object] = {}
    if role:
        filters["vacancy.role"] = role
    if grade:
        filters["vacancy.grade"] = grade
    if has_deadline is True:
        filters["vacancy.application_deadline"] = {"$exists": True, "$ne": ""}
    elif has_deadline is False:
        filters["$or"] = [
            {"vacancy.application_deadline": {"$exists": False}},
            {"vacancy.application_deadline": ""},
            {"vacancy.application_deadline": None},
        ]

    docs = await repo.list_requests(filters=filters)
    return [RequestInDB.model_validate(serialize_document(doc)) for doc in docs]


async def get_request_by_id(
    db: AsyncIOMotorDatabase,
    *,
    request_id: str,
) -> RequestInDB:
    repo = RequestRepository(db)
    request = await repo.get_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return RequestInDB.model_validate(serialize_document(request))


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


async def update_request_status(
    db: AsyncIOMotorDatabase,
    *,
    request_id: str,
    status_value: RequestStatus | None,
    on_hold: bool | None,
) -> RequestStatusResponse:
    repo = RequestRepository(db)
    request = await repo.get_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if status_value is None and on_hold is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Нужно указать status или on_hold",
        )

    update_payload: dict[str, object] = {}
    current_status_raw = request.get("status")
    max_stage_raw = request.get("max_stage")
    max_stage = int(max_stage_raw) if isinstance(max_stage_raw, int) else 0

    if status_value is not None:
        if not current_status_raw:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Текущий статус заявки не задан",
            )
        try:
            current_status = RequestStatus(current_status_raw)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Текущий статус заявки недопустим",
            )

        check = can_transition(current_status, status_value, max_stage=max_stage)
        if not check.allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=check.reason or "Недопустимый переход статуса",
            )

        if current_status != status_value:
            update_payload["status"] = status_value.value
            if not is_cancel_status(status_value):
                next_stage = stage(status_value)
                if next_stage > max_stage:
                    update_payload["max_stage"] = next_stage

    if on_hold is not None:
        update_payload["on_hold"] = bool(on_hold)

    if not update_payload:
        return RequestStatusResponse.model_validate(serialize_document(request))

    updated = await repo.update_by_id(request_id, update_payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return RequestStatusResponse.model_validate(serialize_document(updated))


async def backfill_request_status_fields(db: AsyncIOMotorDatabase) -> int:
    repo = RequestRepository(db)
    docs = await repo.list_status_backfill_candidates(
        [status.value for status in RequestStatus]
    )
    updated_count = 0
    for doc in docs:
        update_payload: dict[str, object] = {}
        if "on_hold" not in doc:
            update_payload["on_hold"] = False
        status_raw = doc.get("status")
        status_value: RequestStatus | None = None
        if isinstance(status_raw, str) and status_raw:
            try:
                status_value = RequestStatus(status_raw)
            except ValueError:
                status_value = None
        if status_value is None:
            status_value = RequestStatus.NEW
            update_payload["status"] = status_value.value
        if "max_stage" not in doc:
            next_stage = stage(status_value)
            update_payload["max_stage"] = next_stage if next_stage >= 0 else 0
        if update_payload:
            await repo.update_by_id(str(doc.get("_id")), update_payload)
            updated_count += 1
    return updated_count
