from fastapi import APIRouter, HTTPException

from app.schemas.auth import AccessTokenResponse, LoginPayload

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    payload: LoginPayload,
) -> AccessTokenResponse:
    raise HTTPException(status_code=410, detail="Password auth disabled")
