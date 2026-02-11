from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from fastapi import HTTPException

from app.repositories.role import RoleRepository
from pymongo.errors import DuplicateKeyError
from app.schemas.role import (
    RoleDeleteResponse,
    RoleInDB,
    RoleListResponse,
    RolesCreatePayload,
    RolesCreateResponse,
)
from app.utils.mongo import serialize_document


async def list_roles(
    db: AsyncIOMotorDatabase,
    *,
    q: str | None = None,
) -> RoleListResponse:
    repo = RoleRepository(db)
    docs = await repo.list_roles()
    if q:
        q_lower = q.strip().lower()
        docs = [
            doc
            for doc in docs
            if isinstance(doc.get("name"), str)
            and q_lower in doc.get("name").lower()
        ]
    items = [RoleInDB.model_validate(serialize_document(doc)) for doc in docs]
    return RoleListResponse(items=items)


async def role_exists(
    db: AsyncIOMotorDatabase,
    *,
    name: str,
) -> bool:
    repo = RoleRepository(db)
    existing = await repo.get_by_name(name)
    return existing is not None


async def create_roles(
    db: AsyncIOMotorDatabase,
    *,
    payload: RolesCreatePayload,
) -> RolesCreateResponse:
    if not payload.roles:
        raise HTTPException(status_code=422, detail="Список ролей пустой")
    normalized: list[str] = []
    for item in payload.roles:
        if not isinstance(item, str):
            raise HTTPException(status_code=422, detail="Название роли должно быть строкой")
        name = item.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Название роли не должно быть пустым")
        if len(name) > 60:
            raise HTTPException(
                status_code=422,
                detail="Название роли не должно быть длиннее 60 символов",
            )
        normalized.append(name)

    unique = list(dict.fromkeys(normalized))
    repo = RoleRepository(db)
    created_names: list[str] = []
    for name in unique:
        try:
            await repo.create({"name": name, "created_at": datetime.utcnow()})
            created_names.append(name)
        except DuplicateKeyError:
            continue
    return RolesCreateResponse(roles=created_names)


async def delete_role(
    db: AsyncIOMotorDatabase,
    *,
    role_id: str,
) -> RoleDeleteResponse:
    repo = RoleRepository(db)
    deleted = await repo.delete_by_id(role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    return RoleDeleteResponse(id=role_id, deleted=True)
