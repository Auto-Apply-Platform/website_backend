from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.dependencies import get_db
from app.schemas.role import (
    RoleDeleteResponse,
    RoleInDB,
    RoleListResponse,
    RolesCreatePayload,
    RolesCreateResponse,
)
from app.services.roles import create_roles, delete_role, list_roles

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=RoleListResponse)
async def get_roles(
    db: AsyncIOMotorDatabase = Depends(get_db),
    q: str | None = Query(None),
) -> RoleListResponse:
    return await list_roles(db, q=q)


@router.post("", response_model=RolesCreateResponse, status_code=201)
async def post_role(
    payload: RolesCreatePayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RolesCreateResponse:
    return await create_roles(db, payload=payload)


@router.delete("/{role_id}", response_model=RoleDeleteResponse)
async def delete_role_endpoint(
    role_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RoleDeleteResponse:
    if not ObjectId.is_valid(role_id):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор")
    return await delete_role(db, role_id=role_id)
