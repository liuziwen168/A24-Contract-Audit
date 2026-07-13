# app/utils/exceptions.py

from typing import Optional, Any, Dict
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """业务异常基类"""
    
    def __init__(
        self,
        code: int = 1000,
        message: str = "业务异常",
        data: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(self.message)


class AIException(BusinessException):
    """AI服务异常"""
    
    def __init__(
        self,
        message: str = "AI服务异常",
        detail: Optional[str] = None
    ):
        super().__init__(
            code=2001,
            message=message,
            data={"detail": detail} if detail else {}
        )


class JSONParseException(BusinessException):
    """JSON解析异常"""
    
    def __init__(
        self,
        message: str = "AI返回JSON解析失败",
        raw_content: Optional[str] = None
    ):
        super().__init__(
            code=2002,
            message=message,
            data={"raw": raw_content[:500] if raw_content else None}
        )


class ContractValidationException(BusinessException):
    """合同验证异常"""
    
    def __init__(self, message: str = "合同文本验证失败"):
        super().__init__(
            code=3001,
            message=message
        )


class RateLimitException(BusinessException):
    """限流异常"""
    
    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(
            code=4001,
            message=message
        )


# ============================================================
# FastAPI 异常处理器
# ============================================================

def create_exception_response(
    code: int,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    创建统一的异常响应格式
    
    格式与 BaseResponse 保持一致
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": data
        }
    )


async def business_exception_handler(
    request: Request,
    exc: BusinessException
) -> JSONResponse:
    """业务异常处理器"""
    
    logger.warning(
        f"业务异常 - path: {request.url.path}, "
        f"code: {exc.code}, "
        f"message: {exc.message}"
    )
    
    # 业务异常返回200，通过code区分
    return create_exception_response(
        code=exc.code,
        message=exc.message,
        data=exc.data,
        status_code=status.HTTP_200_OK
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """HTTP异常处理器"""
    
    logger.error(
        f"HTTP异常 - path: {request.url.path}, "
        f"status: {exc.status_code}, "
        f"detail: {exc.detail}"
    )
    
    return create_exception_response(
        code=exc.status_code,
        message=str(exc.detail),
        status_code=exc.status_code
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """请求参数验证异常处理器"""
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"参数验证失败 - path: {request.url.path}, "
        f"errors: {errors}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 4000,
            "message": "请求参数验证失败",
            "data": {"errors": errors}
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """通用异常处理器（兜底）"""
    
    logger.error(
        f"未捕获的异常 - path: {request.url.path}, "
        f"error: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 9999,
            "message": "系统内部错误",
            "data": {
                "error": str(exc) if logger.level == logging.DEBUG else None
            }
        }
    )