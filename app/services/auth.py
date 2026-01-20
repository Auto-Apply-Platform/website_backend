from datetime import datetime, timedelta

import jwt

from app.core.config import settings


def create_access_token(telegram_user_id: int) -> str:
    expire_at = datetime.utcnow() + timedelta(
        seconds=settings.access_token_expires_seconds,
    )
    payload = {
        "sub": f"tg:{telegram_user_id}",
        "tg_id": telegram_user_id,
        "exp": expire_at,
    }
    return jwt.encode(
        payload,
        settings.auth_jwt_secret,
        algorithm=settings.auth_jwt_alg,
    )
