from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, health, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(health.router, tags=["health"])
