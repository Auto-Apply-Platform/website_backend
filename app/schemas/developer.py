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
    full_name: str | None = None
    main_stack: str | None = None
    role: str | None = None
    grade: str | None = None
    grade_raw: str | None = None
    experience_years: float | None = None
    stack: DeveloperStack | None = None
    work_format: str | None = None
    employment_type: str | None = None
    location: str | None = None
    salary_expectations: str | None = None
    education_level: str | None = None
    additional_information: str | None = None


class DeveloperUpdate(BaseModel):
    full_name: str | None = None
    main_stack: str | None = None
    grade: str | None = None
    resume_path: str | None = None
    parsing_status: str | None = None


class DeveloperPatchPayload(BaseModel):
    full_name: str | None = None
    role: Literal[
        "Backend Developer",
        "Frontend Developer",
        "Fullstack Developer",
        "Mobile Developer",
        "Data Engineer",
        "Data Analyst",
        "Machine Learning Engineer",
        "UI/UX designer",
        "1С разработчик",
        "Другое",
    ] | None = None
    grade: Literal["Junior", "Middle", "Senior"] | None = None
    grade_raw: str | None = None
    experience_years: float | None = None
    stack: DeveloperStack | None = None
    work_format: Literal["Remote", "Hybrid", "Office"] | None = None
    employment_type: str | None = None
    location: str | None = None
    salary_expectations: str | None = None
    education_level: str | None = None
    additional_information: str | None = None


class DeveloperDeletePayload(BaseModel):
    ids: list[str]


class DeveloperDeleteResponse(BaseModel):
    delete_ids: list[str]
    not_found_ids: list[str]
    invalid_ids: list[str]


class DeveloperListItem(BaseModel):
    id: str
    full_name: str
    role: str
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
