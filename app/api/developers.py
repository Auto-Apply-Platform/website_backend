from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.consts import DEFAULT_PAGE_SIZE
from app.dependencies import get_db
from app.repositories.developer import DeveloperRepository
from app.schemas.developer import (
    DeveloperCreate,
    DeveloperDeletePayload,
    DeveloperDeleteResponse,
    DeveloperInDB,
    DeveloperListResponse,
)
from app.utils.files import save_upload
from app.core.config import settings

router = APIRouter(prefix="/developers", tags=["developers"])


@router.get("/", response_model=DeveloperListResponse)
async def list_developers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    q: str | None = Query(None, min_length=1),
) -> DeveloperListResponse:
    repo = DeveloperRepository(db)
    skip = offset if offset is not None else (page - 1) * size
    filters = {}
    if q:
        filters["full_name"] = {"$regex": q, "$options": "i"}
    items = await repo.list(
        skip=skip,
        limit=size,
        sort=[("created_at", -1)],
        filters=filters,
    )
    total = await repo.count(filters=filters)
    return DeveloperListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.post("/", response_model=DeveloperInDB)
async def create_developer(
    full_name: str = Form(...),
    main_stack: str = Form(...),
    grade: str = Form(...),
    resume: list[UploadFile] = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, object]:
    try:
        if len(resume) != 1:
            raise HTTPException(
                status_code=400,
                detail="Разрешен только один файл резюме",
            )
        resume_path = await save_upload(resume[0], settings.uploads_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    developer = DeveloperCreate(
        full_name=full_name,
        main_stack=main_stack,
        grade=grade,
        resume_path=resume_path,
    )
    payload = developer.model_dump()
    repo = DeveloperRepository(db)
    return await repo.create(payload)


@router.post("/delete", response_model=DeveloperDeleteResponse)
async def delete_developers(
    payload: DeveloperDeletePayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DeveloperDeleteResponse:
    if not payload.ids:
        raise HTTPException(
            status_code=400,
            detail="Список идентификаторов не должен быть пустым",
        )
    repo = DeveloperRepository(db)
    deleted_ids: list[str] = []
    not_found_ids: list[str] = []
    invalid_ids: list[str] = []

    for developer_id in payload.ids:
        if not ObjectId.is_valid(developer_id):
            invalid_ids.append(developer_id)
            continue
        deleted = await repo.delete_by_id(developer_id)
        if deleted:
            deleted_ids.append(developer_id)
        else:
            not_found_ids.append(developer_id)

    if invalid_ids or not_found_ids:
        detail = {"invalid_ids": invalid_ids, "not_found_ids": not_found_ids}
        if not invalid_ids:
            detail.pop("invalid_ids")
        if not not_found_ids:
            detail.pop("not_found_ids")
        raise HTTPException(status_code=400, detail=detail)

    return DeveloperDeleteResponse(
        delete_ids=deleted_ids,
        not_found_ids=[],
        invalid_ids=[],
    )


@router.delete("/{developer_id}", status_code=204)
async def delete_developer(
    developer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(
            status_code=400,
            detail="Некорректный идентификатор",
        )
    repo = DeveloperRepository(db)
    deleted = await repo.delete_by_id(developer_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
