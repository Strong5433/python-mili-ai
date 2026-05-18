from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import BaseResponse, success_response
from app.dependencies import (
    get_chat_history_service,
    get_db_session,
    get_login_user,
    require_role,
)
from app.models.user import User
from app.schemas.chat_history import ChatHistoryQueryRequest, PageChatHistory
from app.services.chat_history_service import ChatHistoryService
from app.services.user_service import USER_ROLE_ADMIN

router = APIRouter(prefix="/chatHistory", tags=["chatHistory"])


@router.get("/app/{app_id}", response_model=BaseResponse[PageChatHistory])
async def list_app_chat_history(
    app_id: int = Path(gt=0),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    last_create_time: datetime | None = Query(default=None, alias="lastCreateTime"),
    login_user: User = Depends(get_login_user),
    db: AsyncSession = Depends(get_db_session),
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
) -> BaseResponse[PageChatHistory]:
    page = await chat_history_service.list_app_chat_history(
        db=db,
        app_id=app_id,
        page_size=page_size,
        last_create_time=last_create_time,
        login_user=login_user,
    )
    return success_response(page)


@router.post("/admin/list/page/vo", response_model=BaseResponse[PageChatHistory])
async def list_chat_history_by_page_for_admin(
    payload: ChatHistoryQueryRequest,
    _: User = Depends(require_role(USER_ROLE_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
) -> BaseResponse[PageChatHistory]:
    page = await chat_history_service.list_chat_history_by_page_for_admin(db, payload)
    return success_response(page)
