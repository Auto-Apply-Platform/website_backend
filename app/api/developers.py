import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.consts import DEFAULT_PAGE_SIZE
from app.dependencies import get_db
from app.schemas.developer import (
    DeveloperInDB,
    DeveloperListResponse,
    DeveloperPatchPayload,
    DeveloperUploadResponse,
)
from app.services.developers import (
    create_developer as create_developer_service,
    delete_developer as delete_developer_service,
    get_developer_by_id,
    get_developer_resume,
    list_developers as list_developers_service,
    update_developer as update_developer_service,
)

router = APIRouter(prefix="/developers", tags=["developers"])
logger = logging.getLogger(__name__)



@router.get("", response_model=DeveloperListResponse)
async def list_developers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    q: str | None = Query(None, min_length=1),
    role: str | None = Query(None),
    grade: str | None = Query(None),
    work_format: str | None = Query(None),
) -> DeveloperListResponse:
    return await list_developers_service(
        db,
        page=page,
        size=size,
        offset=offset,
        q=q,
        role=role,
        grade=grade,
        work_format=work_format,
    )






@router.post("", response_model=DeveloperUploadResponse, status_code=201)
async def create_developer(
    resume: list[UploadFile] = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DeveloperUploadResponse:
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
    return await create_developer_service(db, resume=resume)


@router.get("/{developer_id}", response_model=DeveloperInDB)
async def get_developer(
    developer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DeveloperInDB:
    return await get_developer_by_id(db, developer_id=developer_id)


@router.patch("/{developer_id}", response_model=DeveloperInDB)
async def update_developer(
    developer_id: str,
    payload: DeveloperPatchPayload,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DeveloperInDB:
    return await update_developer_service(
        db,
        developer_id=developer_id,
        payload=payload,
    )


@router.get("/{developer_id}/resume", name="download_resume")
async def download_resume(
    developer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> FileResponse:
    return await get_developer_resume(db, developer_id=developer_id)


@router.delete("/{developer_id}", status_code=204)
async def delete_developer(
    developer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    await delete_developer_service(
        db,
        developer_id=developer_id,
    )
