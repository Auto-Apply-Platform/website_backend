from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.clients.mongo import mongo_client
from app.core.config import settings


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    db = mongo_client.connect()
    try:
        yield db
    finally:
        pass


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, object]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[settings.auth_jwt_alg],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail="Срок действия токена истек",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail="Недействительный токен",
        ) from exc
    tg_id = payload.get("tg_id")
    if tg_id is None:
        sub = payload.get("sub")
        if isinstance(sub, str) and sub.startswith("tg:"):
            tg_id_part = sub.split("tg:", 1)[1]
            if tg_id_part.isdigit():
                tg_id = int(tg_id_part)
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    return {"tg_id": tg_id}
