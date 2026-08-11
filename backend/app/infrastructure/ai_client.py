from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.core.errors import fail
from app.schemas.ai import AIReviewResult

logger = logging.getLogger(__name__)


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
                
                body = response.json()
                
                # 打印完整的响应内容，用于调试
                logger.info(f"AI服务响应状态码: {response.status_code}")
                logger.info(f"AI服务响应内容: {json.dumps(body, ensure_ascii=False, indent=2)[:3000]}")
                
                # AI 服务用 HTTP 200 返回业务错误，先检查业务 code
                if isinstance(body, dict) and body.get("code") != "OK":
                    err_data = body.get("data")
                    err_code = err_data.get("code") if isinstance(err_data, dict) else None
                    err_message = err_data.get("message") if isinstance(err_data, dict) else None
                    logger.error(f"AI服务返回业务错误: code={err_code}, message={err_message}")
                    raise AIClientError(err_code or "AI_SERVICE_ERROR")
                    
                if response.status_code >= 400:
                    logger.error(f"AI服务HTTP错误: {response.status_code}")
                    raise AIClientError("REVIEW_FAILED")
                    
                try:
                    # 从 API 信封中提取实际数据
                    inner = body["data"] if isinstance(body, dict) and "data" in body else body
                    
                    # 打印提取后的数据，用于调试
                    logger.info(f"提取的inner数据: {json.dumps(inner, ensure_ascii=False, indent=2)[:2000]}")
                    
                    return AIReviewResult.model_validate(inner)
                    
                except ValidationError as e:
                    # 详细打印每个字段的验证错误
                    logger.error("=" * 60)
                    logger.error("Pydantic 验证失败 - 详细错误:")
                    for error in e.errors():
                        loc_str = " -> ".join(str(loc) for loc in error['loc'])
                        logger.error(f"  字段路径: {loc_str}")
                        logger.error(f"    错误类型: {error['type']}")
                        logger.error(f"    错误信息: {error['msg']}")
                        if 'input' in error:
                            logger.error(f"    实际值: {error['input']}")
                        logger.error("-" * 40)
                    logger.error("=" * 60)
                    logger.error(f"完整数据: {json.dumps(inner, ensure_ascii=False, indent=2)}")
                    raise AIClientError("AI_RESPONSE_INVALID")
                    
                except (ValueError, KeyError) as e:
                    logger.error(f"数据提取失败: {e}")
                    logger.error(f"原始body: {json.dumps(body, ensure_ascii=False, indent=2)}")
                    raise AIClientError("AI_RESPONSE_INVALID")
                    
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                logger.warning(f"AI服务网络错误 (尝试 {attempt + 1}/{settings.ai_retry_count + 1}): {e}")
                if attempt < settings.ai_retry_count:
                    await self.sleep(settings.ai_retry_base_seconds * (2**attempt))
                    continue
                raise AIClientError("AI_SERVICE_UNAVAILABLE")
                
        raise AIClientError("AI_SERVICE_UNAVAILABLE")