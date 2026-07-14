from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

from app.core.config import settings
from app.core.errors import fail

IMAGE_SIGNATURES = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"II*\x00",
    b"MM\x00*",
)


def file_type(name: str, content: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf" and content.startswith(b"%PDF-"):
        return "pdf"
    if suffix == ".docx" and content.startswith(b"PK"):
        try:
            with zipfile.ZipFile(__import__("io").BytesIO(content)) as archive:
                if (
                    "[Content_Types].xml" in archive.namelist()
                    and "word/document.xml" in archive.namelist()
                ):
                    return "docx"
        except zipfile.BadZipFile:
            pass
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff"} and content.startswith(
        IMAGE_SIGNATURES
    ):
        return "image"
    raise fail("FILE_TYPE_UNSUPPORTED")


def safe_name(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._")
    return cleaned[:255] or "upload"


def save_upload(contract_id: int, original_name: str, content: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(content).hexdigest()
    target = settings.upload_root.resolve() / str(contract_id)
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{digest}_{safe_name(original_name)}"
    path.write_bytes(content)
    return str(path), digest
