from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.core.errors import fail
from app.schemas.ai import AIReviewResult


class AIClientError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class AIClient:
    def __init__(self, sleep: Callable[[float], Awaitable[None]] = asyncio.sleep):
        self.sleep = sleep

    async def health(self) -> dict[str, object]:
        parts = urlsplit(settings.ai_service_base_url)
        url = urlunsplit((parts.scheme, parts.netloc, "/health", "", ""))
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=5)) as client:
                response = await client.get(
                    url, headers={"X-Internal-Token": settings.ai_internal_token}
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError):
            raise fail("AI_SERVICE_UNAVAILABLE")

    async def review_full(self, payload: dict[str, object]) -> AIReviewResult:
        url = f"{settings.ai_service_base_url.rstrip('/')}/reviews/full"
        headers = {
            "X-Internal-Token": settings.ai_internal_token,
            "X-Request-Id": str(payload["requestId"]),
        }
        for attempt in range(settings.ai_retry_count + 1):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=5)) as client:
                    response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < settings.ai_retry_count:
                        await self.sleep(settings.ai_retry_base_seconds * (2**attempt))
                        continue
                    raise AIClientError("AI_SERVICE_UNAVAILABLE")
                if response.status_code >= 400:
                    raise AIClientError("REVIEW_FAILED")
                try:
                    return AIReviewResult.model_validate(response.json())
                except (ValidationError, ValueError):
                    raise AIClientError("AI_RESPONSE_INVALID")
            except (httpx.NetworkError, httpx.TimeoutException):
                if attempt < settings.ai_retry_count:
                    await self.sleep(settings.ai_retry_base_seconds * (2**attempt))
                    continue
                raise AIClientError("AI_SERVICE_UNAVAILABLE")
        raise AIClientError("AI_SERVICE_UNAVAILABLE")
