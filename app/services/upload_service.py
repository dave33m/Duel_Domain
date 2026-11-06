"""Storage for uploaded images.

Files are written to ``UPLOAD_DIR/banners`` and served by the ``/uploads`` static mount.
The extension is derived from the file bytes rather than the client's filename or
content type, so an upload can't escape the directory or claim a non-image type.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

BANNER_SUBDIR = "banners"


def _detect_extension(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


class UploadService:
    @staticmethod
    async def save_banner(file: UploadFile) -> str:
        """Save a banner image and return its public path, e.g. ``/uploads/banners/<id>.png``."""
        data = await file.read(settings.MAX_BANNER_BYTES + 1)
        if not data:
            raise ValueError("Uploaded file is empty")
        if len(data) > settings.MAX_BANNER_BYTES:
            raise ValueError(
                f"Banner must be {settings.MAX_BANNER_BYTES // (1024 * 1024)} MB or smaller"
            )

        extension = _detect_extension(data)
        if extension is None:
            raise ValueError("Banner must be a PNG, JPEG, WebP or GIF image")

        directory = Path(settings.UPLOAD_DIR) / BANNER_SUBDIR
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{extension}"
        (directory / filename).write_bytes(data)
        return f"/uploads/{BANNER_SUBDIR}/{filename}"
