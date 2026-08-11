"""FastAPI应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"AI服务启动 - 版本: {settings.APP_VERSION}")
    logger.info(f"Qwen模型: {settings.QWEN_MODEL}")
    yield
    logger.info("AI服务关闭")


def create_app() -> FastAPI:
    app = FastAPI(
        title="A24合同智能审核AI服务",
        description="基于大模型的企业合同智能审核与风险预警系统 - AI服务",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes.router)
    setup_exception_handlers(app)

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "model": settings.QWEN_MODEL
        }

    return app


app = create_app()
