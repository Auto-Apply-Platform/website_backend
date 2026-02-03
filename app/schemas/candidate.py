from datetime import datetime

from pydantic import BaseModel


class CandidateInDB(BaseModel):
    id: str
    request_id: str
    developer_id: str
    score: float | None = None
    description: str | None = None
    created_at: datetime | None = None
