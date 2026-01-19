from datetime import datetime

from pydantic import BaseModel, Field


class LogCreate(BaseModel):
    function_name: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LogInDB(LogCreate):
    id: str
