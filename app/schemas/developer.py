from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DeveloperStack(BaseModel):
    core: list[str]
    additional: list[str]


class DeveloperCreate(BaseModel):
    full_name: str
    main_stack: str
    grade: str
    resume_path: str
    parsing_status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeveloperUploadResponse(BaseModel):
    id: str
    resume_path: str
    parsing_status: str


class DeveloperInDB(BaseModel):
    id: str
    resume_path: str | None = None
    parsing_status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    full_name: str | None = None
    role: str | None = None
    status: str | None = None
    grade: str | None = None
    experience_years: float | None = None
    stack: DeveloperStack | None = None
    work_format: str | None = None
    location: str | None = None
    rate: str | None = None
    resume_text: str | None = None


class DeveloperUpdate(BaseModel):
    full_name: str | None = None
    main_stack: str | None = None
    grade: str | None = None
    resume_path: str | None = None
    parsing_status: str | None = None


class DeveloperPatchPayload(BaseModel):
    full_name: str | None = None
    role: str | None = None
    status: Literal["занят", "доступен", "нужна ротация"] | None = None
    grade: Literal["junior", "middle", "senior", "team_lead"] | None = None
    experience_years: float | None = None
    stack: DeveloperStack | None = None
    work_format: Literal["remote", "hybrid", "office"] | None = None
    location: str | None = None
    rate: str | None = None
    resume_text: str | None = None


class DeveloperListItem(BaseModel):
    id: str
    full_name: str
    role: str
    status: str | None = None
    rate: str | None = None
    stack: DeveloperStack
    experience: float
    parsing_status: str
    created_at: str
    grade: str
    work_format: str


class DeveloperListResponse(BaseModel):
    items: list[DeveloperListItem]
    total: int
    page: int
    size: int


class DeveloperOptionsResponse(BaseModel):
    options: list[str]
