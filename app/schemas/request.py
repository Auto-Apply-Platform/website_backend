from datetime import datetime

from pydantic import BaseModel, Field


class RequestCreate(BaseModel):
    source: str
    message_link: str | None = None
    text: str
    stage_id: str
    position: str | None = None
    grade: str | None = None
    technologies: str | None = None
    experience: str | None = None
    requirements: str | None = None
    responsibilities: str | None = None
    rate: str | None = None
    duration: str | None = None
    project: str | None = None
    location: str | None = None
    additional_requirements: str | None = None
    other: str | None = None
    comment: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RequestInDB(BaseModel):
    id: str
    source: str
    message_link: str | None = None
    text: str
    stage_id: str
    position: str | None = None
    grade: str | None = None
    technologies: str | None = None
    experience: str | None = None
    requirements: str | None = None
    responsibilities: str | None = None
    rate: str | None = None
    duration: str | None = None
    project: str | None = None
    location: str | None = None
    additional_requirements: str | None = None
    other: str | None = None
    comment: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RequestUpdate(BaseModel):
    source: str | None = None
    message_link: str | None = None
    text: str | None = None
    stage_id: str | None = None
    position: str | None = None
    grade: str | None = None
    technologies: str | None = None
    experience: str | None = None
    requirements: str | None = None
    responsibilities: str | None = None
    rate: str | None = None
    duration: str | None = None
    project: str | None = None
    location: str | None = None
    additional_requirements: str | None = None
    other: str | None = None
    comment: str | None = None
