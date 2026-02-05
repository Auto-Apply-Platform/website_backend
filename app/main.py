from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.repositories.candidate import CandidateRepository
from app.repositories.response import ResponseRepository
from app.repositories.role import RoleRepository
from app.repositories.request import RequestRepository
from app.clients.mongo import mongo_client
from app.core.config import settings
from app.repositories.telegram_login_session import (
    TelegramLoginSessionRepository,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    mongo_client.connect()
    db = mongo_client.connect()
    tg_repo = TelegramLoginSessionRepository(db)
    await tg_repo.ensure_indexes()
    try:
        yield
    finally:
        await mongo_client.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.on_event("startup")
async def startup() -> None:
    db = mongo_client.connect()
    role_repo = RoleRepository(db)
    await role_repo.ensure_indexes()
    response_repo = ResponseRepository(db)
    await response_repo.ensure_indexes()
    candidate_repo = CandidateRepository(db)
    await candidate_repo.ensure_indexes()
    request_repo = RequestRepository(db)
    await request_repo.ensure_indexes()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    if (
        exc.status_code == 400
        and exc.detail == "There was an error parsing the body"
        and request.url.path.startswith("/developers")
    ):
        return JSONResponse(
            status_code=400,
            content={"detail": "Разрешен только один файл резюме"},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    translated = []
    for error in exc.errors():
        error_type = error.get("type", "")
        if error_type == "missing":
            msg = "Поле обязательно"
        elif error_type == "string_too_long":
            msg = "name не может быть длиннее 150 символов"
        else:
            msg = "Некорректное значение"
        translated.append(
            {
                "loc": error.get("loc", []),
                "msg": msg,
                "type": error_type,
            }
        )
    return JSONResponse(status_code=422, content={"detail": translated})
