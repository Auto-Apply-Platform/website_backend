import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.consts import DEFAULT_PAGE_SIZE
from app.dependencies import get_db
from app.repositories.developer import DeveloperRepository
from app.schemas.developer import (
    DeveloperDeletePayload,
    DeveloperDeleteResponse,
    DeveloperInDB,
    DeveloperListItem,
    DeveloperListResponse,
    DeveloperPatchPayload,
    DeveloperUploadResponse,
)
from app.utils.files import (
    FileTooLargeError,
    MissingFileError,
    UnsupportedFileTypeError,
    UploadValidationError,
    delete_upload,
    save_upload,
)
from app.core.config import settings
from app.services.developer_parsing import run_resume_parsing
from app.services.resume_parser import determine_parsing_status

router = APIRouter(prefix="/developers", tags=["developers"])
logger = logging.getLogger(__name__)

MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("", response_model=DeveloperListResponse)
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
    developers = await repo.list(
        skip=skip,
        limit=size,
        sort=[("created_at", -1)],
        filters=filters,
    )
    items: list[DeveloperListItem] = []
    for developer in developers:
        stack = developer.get("stack") or {}
        created_at = developer.get("created_at") or ""
        experience = developer.get("experience_years")
        experience_value = (
            float(experience) if isinstance(experience, (int, float)) else 0.0
        )
        full_name = developer.get("full_name") or ""
        role = developer.get("role") or ""
        grade = developer.get("grade")
        work_format = developer.get("work_format")
        parsing_status = developer.get("parsing_status") or ""
        items.append(
            DeveloperListItem(
                id=developer.get("id") or "",
                full_name=full_name,
                role=role,
                stack={
                    "core": stack.get("core") or [],
                    "additional": stack.get("additional") or [],
                },
                experience=experience_value,
                parsing_status=parsing_status,
                created_at=created_at,
                grade=grade or "",
                working_format=work_format or "",
            )
        )
    total = await repo.count(filters=filters)
    return DeveloperListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=DeveloperUploadResponse, status_code=201)
async def create_developer(
    background_tasks: BackgroundTasks,
    resume: list[UploadFile] = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, object]:
    logger.info(
        "Resume upload request: count=%s, files=%s",
        len(resume),
        [
            {
                "filename": file.filename,
                "content_type": file.content_type,
            }
            for file in resume
        ],
    )
    if len(resume) != 1:
        raise HTTPException(
            status_code=422,
            detail="Разрешен только один файл резюме",
        )
    try:
        resume_path, saved_path = await save_upload(
            resume[0],
            settings.uploads_dir,
            max_size_bytes=MAX_RESUME_SIZE_BYTES,
            allowed_extensions=ALLOWED_EXTENSIONS,
            allowed_content_types=ALLOWED_CONTENT_TYPES,
        )
    except MissingFileError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except UploadValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    created_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "resume_path": resume_path,
        "parsing_status": "pending",
        "created_at": created_at,
    }
    repo = DeveloperRepository(db)
    created = await repo.create(payload)
    developer_id = created.get("id")
    if not developer_id:
        raise HTTPException(
            status_code=500,
            detail="Не удалось создать запись резюме",
        )
    background_tasks.add_task(run_resume_parsing, developer_id, saved_path, db)
    return {
        "id": developer_id,
        "resume_path": resume_path,
        "parsing_status": "pending",
    }


@router.get("/{developer_id}", response_model=DeveloperInDB)
async def get_developer(
    developer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, object]:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(
            status_code=400,
            detail="Некорректный идентификатор",
        )
    repo = DeveloperRepository(db)
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
    return developer


@router.patch("/{developer_id}", response_model=DeveloperInDB)
async def update_developer(
    developer_id: str,
    payload: DeveloperPatchPayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, object]:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(
            status_code=400,
            detail="Некорректный идентификатор",
        )
    repo = DeveloperRepository(db)
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
    update_data = payload.model_dump(exclude_unset=True)
    merged = {**developer, **update_data}
    parsing_status = await determine_parsing_status(merged)
    update_data["parsing_status"] = parsing_status
    updated = await repo.update_by_id(developer_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
    return updated


@router.get("/{developer_id}/resume", name="download_resume")
async def download_resume(
    developer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> FileResponse:
    if not ObjectId.is_valid(developer_id):
        raise HTTPException(
            status_code=400,
            detail="Некорректный идентификатор",
        )
    repo = DeveloperRepository(db)
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
    resume_path = developer.get("resume_path")
    if not resume_path:
        raise HTTPException(
            status_code=404,
            detail="Файл резюме не найден",
        )
    filename = Path(resume_path).name
    file_path = Path(settings.uploads_dir) / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Файл резюме не найден",
        )
    extension = file_path.suffix
    full_name = (developer.get("full_name") or "").strip()
    safe_name = full_name.replace("/", "_").replace("\\", "_") if full_name else "resume"
    download_name = f"{safe_name}{extension}"
    return FileResponse(file_path, filename=download_name)


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
        developer = await repo.get_by_id(developer_id)
        if not developer:
            not_found_ids.append(developer_id)
            continue
        try:
            delete_upload(
                developer.get("resume_path"),
                settings.uploads_dir,
            )
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail="Не удалось удалить файл резюме",
            ) from exc
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
    developer = await repo.get_by_id(developer_id)
    if not developer:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
    try:
        delete_upload(
            developer.get("resume_path"),
            settings.uploads_dir,
        )
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Не удалось удалить файл резюме",
        ) from exc
    deleted = await repo.delete_by_id(developer_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Разработчик не найден",
        )
