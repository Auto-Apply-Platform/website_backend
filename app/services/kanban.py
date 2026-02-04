from __future__ import annotations

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.kanban import KanbanResponse
from app.schemas.request_status import RequestStatus
from app.schemas.response_stage import ResponseStage
from app.utils.mongo import serialize_document


async def get_kanban(
    db: AsyncIOMotorDatabase,
    *,
    role: str | None = None,
    grade: str | None = None,
    work_format: str | None = None,
    has_deadline: bool | None = None,
) -> KanbanResponse:
    filters: dict[str, object] = {
        "status": {"$in": [RequestStatus.ACTIVE.value, RequestStatus.ON_HOLD.value]},
    }
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

    requests_cursor = db["requests"].find(filters).sort("created_at", -1)
    requests_by_id: dict[str, dict] = {}
    async for request in requests_cursor:
        request_id = str(request.get("_id"))
        requests_by_id[request_id] = request

    if not requests_by_id:
        return KanbanResponse(requests=[])

    request_ids = list(requests_by_id.keys())
    candidates_cursor = db["candidates"].find({"request_id": {"$in": request_ids}})
    request_ids_with_candidates: set[str] = set()
    async for candidate in candidates_cursor:
        request_id = candidate.get("request_id")
        if isinstance(request_id, str):
            request_ids_with_candidates.add(request_id)

    if not request_ids_with_candidates:
        return KanbanResponse(requests=[])

    responses_cursor = db["responses"].find(
        {"request_id": {"$in": list(request_ids_with_candidates)}}
    )
    responses = [serialize_document(doc) async for doc in responses_cursor]

    developer_ids = {
        response.get("developer_id")
        for response in responses
        if isinstance(response.get("developer_id"), str)
    }
    developer_object_ids = []
    for developer_id in developer_ids:
        try:
            developer_object_ids.append(ObjectId(developer_id))
        except Exception:
            continue
    developers_by_id: dict[str, dict] = {}
    if developer_object_ids:
        developers_cursor = db["developers"].find({"_id": {"$in": developer_object_ids}})
        async for developer in developers_cursor:
            developers_by_id[str(developer.get("_id"))] = developer

    empty_responses_by_stage = {stage: [] for stage in ResponseStage}
    requests_payload: list[dict] = []
    for request_id, request in requests_by_id.items():
        if request_id not in request_ids_with_candidates:
            continue
        vacancy = request.get("vacancy") or {}
        requests_payload.append(
            {
                "id": request_id,
                "name": request.get("name"),
                "status": request.get("status"),
                "application_deadline": vacancy.get("application_deadline"),
                "updated_at": request.get("updated_at"),
                "responses_by_stage": {
                    stage: list(items) for stage, items in empty_responses_by_stage.items()
                },
            }
        )

    requests_index = {item["id"]: item for item in requests_payload}
    for response in responses:
        request_id = response.get("request_id") or ""
        request_item = requests_index.get(request_id)
        if not request_item:
            continue
        developer_id = response.get("developer_id") or ""
        developer = developers_by_id.get(developer_id) or {}
        stage_value = response.get("stage") or ResponseStage.NEW.value
        try:
            stage = ResponseStage(stage_value)
        except ValueError:
            stage = ResponseStage.NEW
        request_item["responses_by_stage"][stage].append(
            {
                "id": response.get("id") or "",
                "developer_id": developer_id,
                "developer_full_name": developer.get("full_name") or "",
                "rate": response.get("rate"),
                "developer_role": developer.get("role"),
                "updated_at": response.get("updated_at"),
            }
        )

    return KanbanResponse(requests=requests_payload)
