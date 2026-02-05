from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.response_stage import ResponseStage
from app.schemas.request import RequestMeta


class ResponseCreatePayload(BaseModel):
    request_id: str
    developer_id: str
    rate: str


class ResponsePatchPayload(BaseModel):
    stage: ResponseStage | None = None
    rate: str | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "ResponsePatchPayload":
        if self.stage is None and self.rate is None:
            raise ValueError("stage or rate is required")
        return self


class ResponseInDB(BaseModel):
    id: str
    request_id: str
    developer_id: str
    rate: str | None = None
    stage: ResponseStage
    max_stage: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResponseWithAllowed(ResponseInDB):
    allowed_stages: list[ResponseStage] = Field(default_factory=list)


class ResponseDeveloper(BaseModel):
    id: str
    full_name: str


class ResponseRequest(BaseModel):
    id: str
    name: str | None = None
    raw_text: str | None = None
    meta: RequestMeta | None = None


class ResponseCandidate(BaseModel):
    score: float | None = None
    description: dict | None = None


class ResponseDetailResponse(BaseModel):
    response: ResponseInDB
    developer: ResponseDeveloper
    request: ResponseRequest
    candidate: ResponseCandidate | None = None
