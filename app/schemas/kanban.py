from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.response_stage import ResponseStage


class KanbanResponseItem(BaseModel):
    id: str
    developer_id: str
    developer_full_name: str
    rate: str | None = None
    developer_role: str | None = None
    updated_at: datetime | None = None
    allowed_stages: list[ResponseStage] = Field(default_factory=list)


class KanbanRequestItem(BaseModel):
    id: str
    name: str | None = None
    status: str | None = None
    rate: str | None = None
    application_deadline: str | None = None
    updated_at: datetime | None = None
    responses_by_stage: dict[ResponseStage, list[KanbanResponseItem]] = Field(
        default_factory=dict
    )


class KanbanResponse(BaseModel):
    requests: list[KanbanRequestItem]
