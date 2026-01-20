import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.dependencies import get_db
from app.repositories.telegram_login_session import TelegramLoginSessionRepository
from app.schemas.telegram_auth import (
    TelegramConfirmRequest,
    TelegramConfirmResponse,
    TelegramQRRequest,
    TelegramQRResponse,
    TelegramStatusResponse,
)
from app.services.auth import create_access_token

router = APIRouter(prefix="/auth/telegram", tags=["auth"])


@router.post("/qr", response_model=TelegramQRResponse)
async def create_qr(
    payload: TelegramQRRequest | None = Body(default=None),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TelegramQRResponse:
    if not settings.telegram_bot_username:
        raise HTTPException(
            status_code=500,
            detail="TELEGRAM_BOT_USERNAME is not configured",
        )
    login_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(
        seconds=settings.login_token_ttl_seconds,
    )
    redirect_url = payload.redirect_url if payload else None
    session = {
        "_id": login_token,
        "status": "PENDING",
        "telegram_user_id": None,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "consumed": False,
        "denied_reason": None,
        "redirect_url": redirect_url,
    }
    repo = TelegramLoginSessionRepository(db)
    await repo.create_session(session)
    deep_link = (
        f"https://t.me/{settings.telegram_bot_username}?start={login_token}"
    )
    return TelegramQRResponse(
        login_token=login_token,
        expires_in=settings.login_token_ttl_seconds,
        url=deep_link,
    )


@router.get("/status", response_model=TelegramStatusResponse)
async def status(
    login_token: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TelegramStatusResponse:
    repo = TelegramLoginSessionRepository(db)
    session = await repo.get_by_id(login_token)
    if not session:
        raise HTTPException(status_code=404, detail="Login token not found")
    now = datetime.utcnow()
    if session.get("expires_at") and session["expires_at"] <= now:
        raise HTTPException(status_code=410, detail="Login token expired")
    status_value = session.get("status")
    if status_value == "PENDING":
        return TelegramStatusResponse(status="PENDING")
    if status_value == "DENIED":
        return TelegramStatusResponse(
            status="DENIED",
            reason=session.get("denied_reason") or "NOT_ALLOWED",
        )
    if status_value == "APPROVED":
        consumed = await repo.consume_if_approved(login_token)
        if consumed and consumed.get("telegram_user_id") is not None:
            token = create_access_token(consumed["telegram_user_id"])
            return TelegramStatusResponse(
                status="APPROVED",
                access_token=token,
                token_type="Bearer",
                expires_in=settings.access_token_expires_seconds,
            )
        return TelegramStatusResponse(status="APPROVED")
    return TelegramStatusResponse(status="PENDING")


@router.post("/confirm", response_model=TelegramConfirmResponse)
async def confirm(
    payload: TelegramConfirmRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    x_bot_secret: str | None = Header(default=None, alias="X-BOT-SECRET"),
) -> TelegramConfirmResponse:
    if not settings.telegram_bot_secret or x_bot_secret != settings.telegram_bot_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    repo = TelegramLoginSessionRepository(db)
    session = await repo.get_by_id(payload.login_token)
    if not session:
        raise HTTPException(status_code=404, detail="Login token not found")
    now = datetime.utcnow()
    if session.get("expires_at") and session["expires_at"] <= now:
        raise HTTPException(status_code=410, detail="Login token expired")
    if session.get("status") == "DENIED":
        return TelegramConfirmResponse(
            status="DENIED",
            reason=session.get("denied_reason") or "NOT_ALLOWED",
        )
    if session.get("status") == "APPROVED":
        return TelegramConfirmResponse(status="APPROVED")
    allowed = payload.telegram_user_id in settings.tg_whitelist_set
    if not allowed:
        await repo.update_by_token(
            payload.login_token,
            {
                "status": "DENIED",
                "telegram_user_id": payload.telegram_user_id,
                "denied_reason": "NOT_ALLOWED",
            },
        )
        return TelegramConfirmResponse(
            status="DENIED",
            reason="NOT_ALLOWED",
        )
    await repo.update_by_token(
        payload.login_token,
        {
            "status": "APPROVED",
            "telegram_user_id": payload.telegram_user_id,
            "username": payload.username,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "denied_reason": None,
        },
    )
    return TelegramConfirmResponse(status="APPROVED")
    redirect_url = payload.redirect_url if payload else None
