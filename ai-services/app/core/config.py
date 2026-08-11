"""配置管理"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    APP_NAME: str = "A24 Contract Audit AI Service"

    HOST: str = "0.0.0.0"
    PORT: int = 8001
    ALLOWED_ORIGINS: List[str] = ["*"]

    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen3.7-plus")
    QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MAX_TOKENS: int = 8192
    QWEN_TEMPERATURE: float = 0.1

    INTERNAL_TOKEN: str = os.getenv("INTERNAL_TOKEN", "")
    PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "v0.1")

    MAX_FILE_SIZE_MB: int = 20
    OCR_LANGUAGE: str = "ch"
    OCR_USE_GPU: bool = False

    CONNECTION_TIMEOUT: int = 5
    READ_TIMEOUT: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 允许额外字段，忽略它们


settings = Settings()
