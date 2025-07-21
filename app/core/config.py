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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    ALGORITHM: str = "HS256"

    # Refresh Token Configuration
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    REFRESH_TOKEN_COOKIE_SECURE: bool = False  # Set to True in production
    REFRESH_TOKEN_COOKIE_HTTPONLY: bool = True
    REFRESH_TOKEN_COOKIE_SAMESITE: str = "lax"
    REFRESH_TOKEN_COOKIE_PATH: str = "/api/v1/auth"

    # Session Management
    MAX_SESSIONS_PER_USER: int = 5  # Limit concurrent sessions
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24

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

    # Celery Background Tasks (Optional)
    ENABLE_CELERY: bool = False
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000

    # Celery Test Configuration (for eager execution)
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_TASK_EAGER_PROPAGATES: bool = False

    # Rate Limiting
    ENABLE_RATE_LIMITING: bool = False
    RATE_LIMIT_STORAGE_BACKEND: str = "memory"  # "memory" or "redis"

    # Rate Limit Defaults (requests per minute)
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_EMAIL_VERIFICATION: str = "3/minute"
    RATE_LIMIT_PASSWORD_RESET: str = "3/minute"
    RATE_LIMIT_OAUTH: str = "10/minute"
    RATE_LIMIT_ACCOUNT_DELETION: str = "3/minute"

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

    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1  # 1 hour for security

    # Account Deletion (GDPR compliance)
    # 24 hours for deletion confirmation
    ACCOUNT_DELETION_TOKEN_EXPIRE_HOURS: int = 24
    # 7 days grace period before permanent deletion
    ACCOUNT_DELETION_GRACE_PERIOD_DAYS: int = 7
    # Send reminders 3 and 1 days before deletion
    ACCOUNT_DELETION_REMINDER_DAYS: list[int] = [3, 1]

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

    # Error Monitoring (GlitchTip/Sentry)
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% of profiles

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
