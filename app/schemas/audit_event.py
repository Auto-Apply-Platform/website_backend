from datetime import datetime

from pydantic import BaseModel


class AuditEventInDB(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    payload_json: dict
    created_at: datetime | None = None
