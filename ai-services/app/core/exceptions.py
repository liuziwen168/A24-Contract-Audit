"""自定义异常和异常处理"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.response import ErrorResponse


class AIException(Exception):
    def __init__(self, code: str, message: str, detail: dict = None):
        self.code = code
        self.message = message
        self.detail = detail or {}
        super().__init__(message)


class FileParseError(AIException):
    def __init__(self, message: str, detail: dict = None):
        super().__init__("FILE_PARSE_FAILED", message, detail)


class OCRFailedError(AIException):
    def __init__(self, message: str, detail: dict = None):
        super().__init__("OCR_FAILED", message, detail)


class LLMCallError(AIException):
    def __init__(self, message: str, detail: dict = None):
        super().__init__("LLM_API_FAILED", message, detail)


class ResponseInvalidError(AIException):
    def __init__(self, message: str, detail: dict = None):
        super().__init__("AI_RESPONSE_INVALID", message, detail)


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(AIException)
    async def ai_exception_handler(request: Request, exc: AIException):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                code=exc.code,
                message=exc.message,
                detail=exc.detail
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message="系统内部异常",
                detail={"error": str(exc)} if settings.APP_ENV != "production" else {}
            ).model_dump()
        )
