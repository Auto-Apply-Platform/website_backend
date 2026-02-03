from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.request_status import RequestStatus
from app.schemas.response_stage import ResponseStage


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


class RequestDeleteResponse(BaseModel):
    id: str
    deleted: bool


class RequestVacancyStack(BaseModel):
    model_config = ConfigDict(extra="allow")

    required: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)


class RequestVacancy(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str = ""
    grade: str | None = None
    grade_raw: str = ""
    stack: RequestVacancyStack = Field(default_factory=RequestVacancyStack)
    experience_years: float | None = None
    responsibilities: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    salary: str = ""
    location: str = ""
    work_format: str | None = None
    duration: str = ""
    application_deadline: str = ""
    contacts: list[str] = Field(default_factory=list)
    additional_information: str = ""


class RequestMetaTelegram(BaseModel):
    model_config = ConfigDict(extra="allow")

    channel_id: int | None = None
    chat_id: int | None = None
    message_id: int | None = None


class RequestMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str | None = None
    telegram: RequestMetaTelegram | None = None


class RequestInDB(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    status: RequestStatus | None = None
    name: str | None = None
    vacancy: RequestVacancy | None = None
    meta: RequestMeta | None = None
    raw_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RequestCandidateDeveloper(BaseModel):
    id: str
    full_name: str
    role: str | None = None
    grade: str | None = None
    work_format: str | None = None


class RequestCandidateItem(BaseModel):
    developer: RequestCandidateDeveloper
    score: float | None = None
    description: str | None = None
    already_assigned: bool = False


class RequestResponseItem(BaseModel):
    id: str
    developer_id: str
    rate: str | None = None
    stage: ResponseStage
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RequestDetailResponse(BaseModel):
    id: str
    status: RequestStatus | None = None
    name: str | None = None
    vacancy: RequestVacancy | None = None
    meta: RequestMeta | None = None
    raw_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    candidates: list[RequestCandidateItem] = Field(default_factory=list)
    responses: list[RequestResponseItem] = Field(default_factory=list)
