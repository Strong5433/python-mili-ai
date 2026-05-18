from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.core.response import BaseResponse, success_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=BaseResponse[dict[str, Any]])
async def health_check(ping: int | None = Query(default=None, ge=0)) -> BaseResponse[dict[str, Any]]:
    settings = get_settings()
    payload = {
        "status": "UP",
        "appName": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependenciesConfigured": {
            "database": bool(settings.database_url),
            "redis": bool(settings.redis_url),
        },
    }
    if ping is not None:
        payload["ping"] = ping
    return success_response(payload)
