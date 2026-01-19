from pydantic import BaseModel


class StageCreate(BaseModel):
    name: str
    comment: str | None = None
    order_index: int = 0


class StageInDB(StageCreate):
    id: str


class StageUpdate(BaseModel):
    name: str | None = None
    comment: str | None = None
    order_index: int | None = None
