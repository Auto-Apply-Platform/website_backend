from fastapi import APIRouter, Depends

from app.api.auth import router as auth_router
from app.api.developers import router as developers_router
from app.api.health import router as health_router
from app.dependencies import get_current_user

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)

protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(developers_router)
api_router.include_router(protected_router)
