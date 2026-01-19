from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.clients.mongo import mongo_client
from app.repositories.user import UserRepository
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, object]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
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
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    return user
