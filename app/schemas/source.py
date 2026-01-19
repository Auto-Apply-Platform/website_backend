from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    chat_id: str
    last_message_id: int = 0
    enabled: bool = True


class SourceInDB(SourceCreate):
    id: str


class SourceUpdate(BaseModel):
    name: str | None = None
    chat_id: str | None = None
    last_message_id: int | None = None
    enabled: bool | None = None
