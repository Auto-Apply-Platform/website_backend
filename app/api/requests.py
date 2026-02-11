from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from bson import ObjectId

from app.schemas.request import (
    RequestDeleteResponse,
    RequestDetailResponse,
    RequestInDB,
    RequestPatchPayload,
)
from app.services.requests import (
    delete_request_by_id,
    get_request_by_id,
    list_requests as list_requests_service,
    update_request,
)

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[RequestInDB])
async def list_requests(
    db: AsyncIOMotorDatabase = Depends(get_db),
    role: str | None = Query(None),
    grade: str | None = Query(None),
    work_format: str | None = Query(None),
    has_deadline: bool | None = Query(None),
) -> list[RequestInDB]:
    return await list_requests_service(
        db,
        role=role,
        grade=grade,
        work_format=work_format,
        has_deadline=has_deadline,
    )


@router.get("/{request_id}", response_model=RequestDetailResponse)
async def get_request(
    request_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RequestDetailResponse:
    return await get_request_by_id(db, request_id=request_id)


@router.delete("/{request_id}", response_model=RequestDeleteResponse)
async def delete_request(
    request_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RequestDeleteResponse:
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=400,
            detail="Некорректный идентификатор",
        )
    return await delete_request_by_id(db, request_id=request_id)


@router.patch(
    "/{request_id}",
    response_model=RequestDetailResponse,
    summary="Обновление заявки",
    description="Обновляет status и/или name",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Заявка не найдена"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Некорректное тело запроса"},
    },
)
async def patch_request(
    request_id: str,
    payload: RequestPatchPayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RequestDetailResponse:
    return await update_request(
        db,
        request_id=request_id,
        status_value=payload.status,
        name=payload.name,
    )
