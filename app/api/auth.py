from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import AccessTokenResponse, LoginPayload
from app.services.auth import create_access_token
from app.services.users import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    payload: LoginPayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AccessTokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_username(payload.username)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    password_hash = user.get("password_hash")
    if not password_hash or not verify_password(
        payload.password,
        password_hash,
    ):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    token = create_access_token(user.get("username", ""))
    return AccessTokenResponse(access_token=token)
