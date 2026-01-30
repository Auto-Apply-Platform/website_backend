from fastapi import APIRouter, Depends

from app.api.auth_telegram import router as auth_telegram_router
from app.api.developers import router as developers_router
from app.api.roles import router as roles_router
from app.api.requests import router as requests_router
from app.dependencies import get_current_user

api_router = APIRouter()
api_router.include_router(auth_telegram_router)

protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(developers_router)
protected_router.include_router(roles_router)
protected_router.include_router(requests_router)
api_router.include_router(protected_router)
