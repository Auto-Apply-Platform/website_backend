from datetime import datetime
from typing import Any

from bson import ObjectId


def serialize_document(document: dict[str, Any]) -> dict[str, Any]:
    data = {**document}
    if "_id" in data:
        data["id"] = str(data.pop("_id"))
    for key, value in data.items():
        if isinstance(value, ObjectId):
            data[key] = str(value)
        elif isinstance(value, datetime):
            data[key] = value.isoformat()
    return data
