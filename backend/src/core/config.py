"""
应用配置模块
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置类"""

    # 应用基础配置
    APP_NAME: str = "AICG内容分发平台"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API配置
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://aicg_user:aicg_password@localhost:5432/aicg_platform",
        env="DATABASE_URL"
    )

    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # JWT配置
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 密码加密
    BCRYPT_ROUNDS: int = 12

    # MinIO配置
    MINIO_ENDPOINT: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "aicg-files"
    MINIO_REGION: str = "us-east-1"

    # 文件上传配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = ["txt", "md", "docx", "epub"]
    UPLOAD_PATH: str = "uploads"

    # 头像上传配置
    AVATAR_BUCKET_NAME: str = "aicg-avatars"
    MAX_AVATAR_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_AVATAR_TYPES: List[str] = ["jpg", "jpeg", "png", "webp"]
    AVATAR_DEFAULT_SIZE: tuple = (200, 200)  # 默认头像尺寸

    # 视频生成配置
    MAX_CONCURRENT_GENERATIONS: int = 10
    DEFAULT_VIDEO_STYLE: str = "cinematic"
    DEFAULT_VOICE_TYPE: str = "female_gentle"
    DEFAULT_BACKGROUND_MUSIC: bool = True
    VIDEO_MAX_SIZE: int = 2 * 1024 * 1024 * 1024  # 2GB

    # Celery配置
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_RESULT_BACKEND"
    )
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300  # 5分钟
    CELERY_TASK_TIME_LIMIT: int = 600  # 10分钟

    # 日志配置
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGGING: bool = True
    LOG_FILE: Optional[str] = None
    COLORED_LOGS: bool = True

    # 监控配置
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090

    # OpenTelemetry配置
    OTEL_SERVICE_NAME: str = "aicg-backend"
    OTEL_RESOURCE_ATTRIBUTES: str = "service.version=1.0.0"
    OTEL_EXPORTER_PROMETHEUS_ENDPOINT: str = "/metrics"

    # 缓存配置
    CACHE_TTL: int = 3600  # 1小时
    CACHE_MAX_SIZE: int = 1000
    CACHE_PREFIX: str = "aicg:"

    # API限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    RATE_LIMIT_ENABLED: bool = True

    # 安全配置
    SESSION_TIMEOUT: int = 1800  # 30分钟
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_TIMEOUT: int = 900  # 15分钟

    # 性能配置
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_POOL_RECYCLE: int = 3600

    # AI服务配置
    DEFAULT_AI_TIMEOUT: int = 60  # 60秒
    MAX_AI_RETRIES: int = 3
    AI_RETRY_DELAY: float = 1.0

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("CORS_ORIGINS必须是字符串或列表")

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def assemble_allowed_file_types(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip().lower() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return [i.lower() for i in v] if isinstance(v, list) else v
        raise ValueError("ALLOWED_FILE_TYPES必须是字符串或列表")

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "testing", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"ENVIRONMENT必须是以下之一: {valid_envs}")
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL必须是以下之一: {valid_levels}")
        return v.upper()

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        """同步数据库URL（用于Alembic）"""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def minio_url(self) -> str:
        """MinIO服务URL"""
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"

    @property
    def minio_bucket(self) -> str:
        """MinIO默认存储桶名称"""
        return self.MINIO_BUCKET_NAME

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """获取应用设置（单例模式）"""
    return Settings()


# 导出设置实例
settings = get_settings()
