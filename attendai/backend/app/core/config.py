"""Конфигурация приложения через Pydantic Settings."""
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── Application ─────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_PORT: int = 8000
    TIMEZONE: str = "Asia/Almaty"

    # ─── Security ────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── Database ────────────────────────────────────────────────
    POSTGRES_DB: str = "attendai"
    POSTGRES_USER: str = "attendai"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── Redis ───────────────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ─── MinIO ───────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_PHOTOS: str = "attendai-photos"
    MINIO_BUCKET_REPORTS: str = "attendai-reports"

    # ─── ML / Face Recognition ───────────────────────────────────
    FACE_RECOGNITION_THRESHOLD: float = 0.6
    CAMERA_PROCESS_INTERVAL: float = 0.5
    ML_MODELS_DIR: str = "/app/ml_models"
    INSIGHTFACE_MODEL: str = "buffalo_l"
    FACE_GPU_ID: int = -1  # -1 = CPU

    # ─── Notifications ───────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "AttendAI"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # ─── Admin ───────────────────────────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@school.edu"
    FIRST_ADMIN_PASSWORD: str = "Admin123!"
    FIRST_ADMIN_NAME: str = "Администратор"

    # ─── CORS ────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # ─── Institution ─────────────────────────────────────────────
    INSTITUTION_NAME: str = "Образовательное учреждение"
    INSTITUTION_SHORT_NAME: str = "ОУ"


settings = Settings()
