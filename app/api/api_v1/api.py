from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, health, users
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(health.router, tags=["health"])

# Conditionally include WebSocket routes if enabled
if settings.ENABLE_WEBSOCKETS:
    from app.api.api_v1.endpoints import ws_demo
    api_router.include_router(ws_demo.router, tags=["websockets"])
