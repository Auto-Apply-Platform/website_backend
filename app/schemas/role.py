from datetime import datetime

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str


class RoleInDB(BaseModel):
    id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RoleListResponse(BaseModel):
    items: list[RoleInDB]


class RoleDeleteResponse(BaseModel):
    id: str
    deleted: bool
