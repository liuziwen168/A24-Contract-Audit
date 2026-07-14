from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root@localhost:3306/a24_contract_audit"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-me")
    jwt_expire_seconds: int = int(os.getenv("JWT_EXPIRE_SECONDS", "3600"))
    ai_service_base_url: str = os.getenv("AI_SERVICE_BASE_URL", "http://localhost:8001/internal/v1")
    ai_internal_token: str = os.getenv("AI_INTERNAL_TOKEN", "development-only-change-me")
    upload_root: Path = Path(os.getenv("UPLOAD_ROOT", "storage/uploads"))
    report_root: Path = Path(os.getenv("REPORT_ROOT", "storage/reports"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    task_executor_enabled: bool = os.getenv("TASK_EXECUTOR_ENABLED", "false").lower() == "true"
    task_poll_seconds: float = float(os.getenv("TASK_POLL_SECONDS", "1"))
    task_stale_seconds: int = int(os.getenv("TASK_STALE_SECONDS", "300"))
    ai_retry_count: int = int(os.getenv("AI_RETRY_COUNT", "2"))
    ai_retry_base_seconds: float = float(os.getenv("AI_RETRY_BASE_SECONDS", "1"))
    report_executor_enabled: bool = (
        os.getenv("REPORT_EXECUTOR_ENABLED", "false").lower() == "true"
    )
    report_task_poll_seconds: float = float(os.getenv("REPORT_TASK_POLL_SECONDS", "1"))
    report_task_stale_seconds: int = int(os.getenv("REPORT_TASK_STALE_SECONDS", "300"))
    report_max_attempts: int = int(os.getenv("REPORT_MAX_ATTEMPTS", "3"))
    cors_origins: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if item.strip()
    )
    trusted_hosts: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv("TRUSTED_HOSTS", "*").split(",")
        if item.strip()
    )
    openapi_enabled: bool = os.getenv(
        "OPENAPI_ENABLED",
        "false" if os.getenv("APP_ENV", "development") == "production" else "true",
    ).lower() == "true"

    def __post_init__(self) -> None:
        if self.app_env != "production":
            return
        unsafe = (
            self.database_url == "mysql+pymysql://root@localhost:3306/a24_contract_audit"
            or self.jwt_secret == "development-only-change-me"
            or self.ai_internal_token == "development-only-change-me"
            or self.trusted_hosts == ("*",)
        )
        if unsafe:
            raise RuntimeError("production secrets, database URL, and trusted hosts are required")


settings = Settings()
