import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.config import settings

logger = logging.getLogger(__name__)


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the FastAPI application."""
    cors_origins = settings.cors_origins_list
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS origins enabled: {cors_origins}")
    else:
        logger.info("CORS origins not configured - CORS middleware disabled")
