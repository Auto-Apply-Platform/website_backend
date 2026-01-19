from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db_stats: dict[str, Any]
