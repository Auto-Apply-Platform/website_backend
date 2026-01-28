from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.request_status import RequestStatus


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


class RequestStatusPatch(BaseModel):
    status: RequestStatus | None = None
    on_hold: bool | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "RequestStatusPatch":
        if self.status is None and self.on_hold is None:
            raise ValueError("status or on_hold is required")
        return self


class RequestStatusResponse(BaseModel):
    id: str
    status: RequestStatus | None = None
    on_hold: bool = False
    max_stage: int = 0


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


class RequestBestCandidate(BaseModel):
    model_config = ConfigDict(extra="allow")

    developer_id: str | None = None
    score: int | float | None = None
    matched_at: datetime | None = None


class RequestInDB(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    status: RequestStatus | None = None
    on_hold: bool = False
    max_stage: int = 0
    vacancy: RequestVacancy | None = None
    meta: RequestMeta | None = None
    best_candidates: list[RequestBestCandidate] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
