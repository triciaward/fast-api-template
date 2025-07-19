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

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:8080",  # Vue default
        "http://localhost:4200",  # Angular default
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(v)


settings = Settings()
