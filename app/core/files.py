import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config.config import settings

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


async def store_upload(upload: UploadFile, namespace: str) -> tuple[str, str, str, int]:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported attachment type")
    content = await upload.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Attachment is too large")
    original = Path(upload.filename or "attachment").name
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", original)
    stored = f"{uuid.uuid4()}-{safe}"
    directory = settings.upload_dir / namespace
    directory.mkdir(parents=True, exist_ok=True)
    (directory / stored).write_bytes(content)
    return original, stored, upload.content_type or "application/octet-stream", len(content)
