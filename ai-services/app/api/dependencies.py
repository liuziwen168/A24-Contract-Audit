"""依赖注入"""
from fastapi import Header, HTTPException, Request

from app.core.config import settings


async def verify_internal_token(
    x_internal_token: str = Header(...)
) -> str:
    if x_internal_token != settings.INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")
    return x_internal_token


async def get_request_id(
    x_request_id: str = Header(...)
) -> str:
    return x_request_id


async def validate_request(request: Request) -> None:
    content_length = request.headers.get("content-length")
    if content_length:
        size_mb = int(content_length) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大允许 {settings.MAX_FILE_SIZE_MB}MB"
            )
