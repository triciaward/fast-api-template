from typing import Optional, Union

from pydantic.functional_validators import field_validator
from pydantic_settings.main import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )

    PROJECT_NAME: str = "FastAPI Template"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI Template with Authentication"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # JWT
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    ALGORITHM: str = "HS256"

    # Superuser Bootstrap
    FIRST_SUPERUSER: Optional[str] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    # Database
    DATABASE_URL: str = (
        "postgresql://postgres:dev_password_123@localhost:5432/fastapi_template"
    )

    # Redis (Optional)
    ENABLE_REDIS: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # WebSockets (Optional)
    ENABLE_WEBSOCKETS: bool = False

    # Rate Limiting
    ENABLE_RATE_LIMITING: bool = False
    RATE_LIMIT_STORAGE_BACKEND: str = "memory"  # "memory" or "redis"

    # Rate Limit Defaults (requests per minute)
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_EMAIL_VERIFICATION: str = "3/minute"
    RATE_LIMIT_OAUTH: str = "10/minute"

    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    FROM_EMAIL: str = "noreply@example.com"
    FROM_NAME: str = "FastAPI Template"

    # Email Verification
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:8080",  # Vue default
        "http://localhost:4200",  # Angular default
    ]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    ENABLE_FILE_LOGGING: bool = False
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FILE_MAX_SIZE: str = "10MB"
    LOG_FILE_BACKUP_COUNT: int = 5
    ENABLE_COLORED_LOGS: bool = True
    LOG_INCLUDE_TIMESTAMP: bool = True
    LOG_INCLUDE_PID: bool = True
    LOG_INCLUDE_THREAD: bool = True

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str):
            # Handle comma-separated string
            if "," in v:
                return [i.strip() for i in v.split(",")]
            # Handle single string
            elif v.strip():
                return [v.strip()]
            # Handle empty string
            return []
        elif isinstance(v, list):
            return v


settings = Settings()
