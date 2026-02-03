from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.schemas.response import (
    ResponseCreatePayload,
    ResponseDetailResponse,
    ResponseInDB,
    ResponsePatchPayload,
)
from app.services.responses import (
    create_response,
    delete_response,
    get_response_detail,
    update_response,
)

router = APIRouter(prefix="/responses", tags=["responses"])


@router.post("", response_model=ResponseInDB, status_code=201)
async def post_response(
    payload: ResponseCreatePayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ResponseInDB:
    return await create_response(db, payload=payload)


@router.patch("/{response_id}", response_model=ResponseInDB)
async def patch_response(
    response_id: str,
    payload: ResponsePatchPayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ResponseInDB:
    return await update_response(
        db,
        response_id=response_id,
        stage=payload.stage,
        rate=payload.rate,
    )


@router.delete(
    "/{response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_response_endpoint(
    response_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    await delete_response(db, response_id=response_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{response_id}", response_model=ResponseDetailResponse)
async def get_response(
    response_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ResponseDetailResponse:
    return await get_response_detail(db, response_id=response_id)
