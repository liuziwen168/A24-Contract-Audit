from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import router
from app.application.report_executor import ReportExecutor
from app.application.review_executor import ReviewExecutor
from app.core.config import settings
from app.core.errors import AppError, fail
from app.core.request_id import client_ip, new_request_id, request_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    review_task: asyncio.Task[None] | None = None
    review_executor: ReviewExecutor | None = None
    report_task: asyncio.Task[None] | None = None
    report_executor: ReportExecutor | None = None
    if settings.task_executor_enabled:
        review_executor = ReviewExecutor()
        review_task = asyncio.create_task(
            review_executor.run_forever(), name="a24-review-executor"
        )
        app.state.review_executor_task = review_task
    if settings.report_executor_enabled:
        report_executor = ReportExecutor()
        report_task = asyncio.create_task(
            report_executor.run_forever(), name="a24-report-executor"
        )
        app.state.report_executor_task = report_task
    try:
        yield
    finally:
        if review_executor:
            review_executor.stop()
        if report_executor:
            report_executor.stop()
        for task in (review_task, report_task):
            if task is None:
                continue
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="A24 Contract Audit Backend",
    version="0.1.0",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.openapi_enabled else None,
    docs_url="/docs" if settings.openapi_enabled else None,
    redoc_url="/redoc" if settings.openapi_enabled else None,
)
if settings.trusted_hosts != ("*",):
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trace_request(request: Request, call_next):
    token = request_id.set(new_request_id())
    ip_token = client_ip.set(request.client.host if request.client else None)
    try:
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id.get()
        return response
    finally:
        client_ip.reset(ip_token)
        request_id.reset(token)


def error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": error.code,
            "message": error.message,
            "data": None,
            "requestId": request_id.get(),
        },
    )


@app.exception_handler(AppError)
async def app_error(_: Request, error: AppError) -> JSONResponse:
    return error_response(error)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return error_response(fail("PARAM_INVALID"))


@app.exception_handler(SQLAlchemyError)
async def database_error(_: Request, __: SQLAlchemyError) -> JSONResponse:
    return error_response(fail("DATABASE_ERROR"))


@app.exception_handler(Exception)
async def unexpected_error(_: Request, __: Exception) -> JSONResponse:
    return error_response(fail("INTERNAL_ERROR"))


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version, "requestId": request_id.get()}


app.include_router(router)
