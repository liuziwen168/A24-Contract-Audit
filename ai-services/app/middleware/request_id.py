# app/middleware/request_id.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件 - 用于追踪请求链路"""
    
    async def dispatch(self, request: Request, call_next):
        # 从header获取或生成新的request_id
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # 存储到request.state中
        request.state.request_id = request_id
        
        # 添加响应头
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id(request: Request) -> str:
    """获取当前请求的request_id"""
    return getattr(request.state, "request_id", "unknown")