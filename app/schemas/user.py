from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str
    password: str


class UserInDB(BaseModel):
    id: str
    username: str
    password_hash: str
    failed_login_attempts: int = 0
    last_failed_login: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserPublic(BaseModel):
    id: str
    username: str
    failed_login_attempts: int = 0
    last_failed_login: datetime | None = None
    created_at: datetime


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
