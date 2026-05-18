from fastapi import APIRouter

from app.api.app import router as app_router
from app.api.chat_history import router as chat_history_router
from app.api.health import router as health_router
from app.api.user import router as user_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(user_router)
api_router.include_router(app_router)
api_router.include_router(chat_history_router)

