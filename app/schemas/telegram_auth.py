from typing import Literal

from pydantic import BaseModel


class TelegramQRRequest(BaseModel):
    redirect_url: str | None = None


class TelegramQRResponse(BaseModel):
    login_token: str
    expires_in: int
    url: str


class TelegramStatusResponse(BaseModel):
    status: Literal["PENDING", "APPROVED", "DENIED"]
    reason: str | None = None
    access_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None


class TelegramConfirmRequest(BaseModel):
    login_token: str
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    allowed: bool


class TelegramConfirmResponse(BaseModel):
    status: Literal["APPROVED", "DENIED"]
    reason: str | None = None
