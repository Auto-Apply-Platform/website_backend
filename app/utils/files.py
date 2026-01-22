from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class UploadValidationError(ValueError):
    pass


class MissingFileError(UploadValidationError):
    pass


class UnsupportedFileTypeError(UploadValidationError):
    pass


class FileTooLargeError(UploadValidationError):
    pass


async def save_upload(
    upload: UploadFile,
    uploads_dir: str,
    *,
    max_size_bytes: int,
    allowed_extensions: set[str],
    allowed_content_types: set[str],
) -> tuple[str, Path]:
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)
    filename = Path(upload.filename or "").name
    if not filename:
        raise MissingFileError("Файл резюме обязателен")
    suffix = Path(filename).suffix.lower()
    if not suffix or suffix not in allowed_extensions:
        raise UnsupportedFileTypeError("Недопустимое расширение файла")
    if upload.content_type not in allowed_content_types:
        raise UnsupportedFileTypeError("Недопустимый тип содержимого файла")

    unique_name = f"{uuid4().hex}{suffix}"
    file_path = Path(uploads_dir) / unique_name
    total_size = 0
    chunk_size = 1024 * 1024

    try:
        with file_path.open("wb") as target:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_size_bytes:
                    raise FileTooLargeError("Размер файла превышает лимит")
                target.write(chunk)
    except FileTooLargeError:
        file_path.unlink(missing_ok=True)
        raise
    except OSError as exc:
        file_path.unlink(missing_ok=True)
        raise UploadValidationError("Не удалось сохранить файл") from exc

    resume_path = f"{Path(uploads_dir).name}/{unique_name}"
    return resume_path, file_path


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
