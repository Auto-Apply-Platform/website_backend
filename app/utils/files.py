from pathlib import Path

from fastapi import UploadFile


async def save_upload(upload: UploadFile, uploads_dir: str) -> str:
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)
    if not upload.filename:
        raise ValueError("Файл резюме обязателен")
    filename = Path(upload.filename).name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise ValueError("Разрешены только файлы .pdf или .docx")
    file_path = Path(uploads_dir) / filename
    contents = await upload.read()
    if not contents:
        raise ValueError("Файл резюме обязателен")
    file_path.write_bytes(contents)
    return f"/{Path(uploads_dir).name}/{filename}"
