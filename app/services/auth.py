from datetime import datetime, timedelta

import jwt

from app.core.config import settings


def create_access_token(subject: str) -> str:
    expire_at = datetime.utcnow() + timedelta(
        minutes=settings.jwt_expire_minutes,
    )
    payload = {"sub": subject, "exp": expire_at}
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
