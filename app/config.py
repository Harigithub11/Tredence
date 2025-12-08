"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://workflow_user:workflow_pass@localhost:5432/workflow_engine"

    # Application
    APP_NAME: str = "Agent Workflow Engine"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Workflow Engine
    MAX_CONCURRENT_RUNS: int = 10
    MAX_WORKFLOW_ITERATIONS: int = 100
    DEFAULT_TIMEOUT: int = 300  # seconds

    # LLM (Optional)
    ENABLE_LLM: bool = False
    GEMINI_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # Redis (Future)
    REDIS_URL: str = "redis://localhost:6379/0"
    ENABLE_CACHE: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
