from app.models.collections import AUDIT_EVENTS_COLLECTION
from app.repositories.base import BaseRepository


class AuditEventRepository(BaseRepository):
    collection_name = AUDIT_EVENTS_COLLECTION
