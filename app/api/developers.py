from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.repositories.developer import DeveloperRepository
from app.schemas.developer import DeveloperCreate, DeveloperInDB
from app.utils.files import save_upload
from app.core.config import settings

router = APIRouter(prefix="/developers", tags=["developers"])


@router.get("/", response_model=list[DeveloperInDB])
async def list_developers(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[dict[str, object]]:
    repo = DeveloperRepository(db)
    return await repo.list()


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
