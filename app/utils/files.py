from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


async def save_upload(upload: UploadFile, uploads_dir: str) -> str:
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)
    if not upload.filename:
        raise ValueError("Файл резюме обязателен")
    filename = Path(upload.filename).name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise ValueError("Разрешены только файлы .pdf или .docx")
    unique_name = f"{uuid4().hex}{suffix}"
    file_path = Path(uploads_dir) / unique_name
    contents = await upload.read()
    if not contents:
        raise ValueError("Файл резюме обязателен")
    file_path.write_bytes(contents)
    return f"/{Path(uploads_dir).name}/{unique_name}"


def delete_upload(resume_path: str | None, uploads_dir: str) -> None:
    if not resume_path:
        return
    filename = Path(resume_path).name
    if not filename:
        return
    file_path = Path(uploads_dir) / filename
    try:
        file_path.unlink()
    except FileNotFoundError:
        return
