from datetime import datetime

from pydantic import BaseModel, Field


class DeveloperCreate(BaseModel):
    full_name: str
    main_stack: str
    grade: str
    resume_path: str
    parsing_status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeveloperInDB(BaseModel):
    id: str
    full_name: str
    main_stack: str
    grade: str
    resume_path: str
    parsing_status: str = "pending"
    created_at: datetime


class DeveloperUpdate(BaseModel):
    full_name: str | None = None
    main_stack: str | None = None
    grade: str | None = None
    resume_path: str | None = None
    parsing_status: str | None = None
