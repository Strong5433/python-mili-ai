from datetime import UTC, datetime
from math import ceil

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.models.app import App
from app.models.chat_history import ChatHistory
from app.models.user import User
from app.schemas.chat_history import ChatHistoryQueryRequest, ChatHistoryVO, PageChatHistory
from app.services.user_service import USER_ROLE_ADMIN

MESSAGE_TYPE_USER = "user"
MESSAGE_TYPE_ASSISTANT = "assistant"


class ChatHistoryService:
    _sortable_fields = {
        "id": ChatHistory.id,
        "createTime": ChatHistory.create_time,
        "updateTime": ChatHistory.update_time,
        "messageType": ChatHistory.message_type,
        "appId": ChatHistory.app_id,
        "userId": ChatHistory.user_id,
    }
    _valid_message_types = {MESSAGE_TYPE_USER, MESSAGE_TYPE_ASSISTANT}

    async def add_chat_message(
        self,
        db: AsyncSession,
        *,
        app_id: int,
        user_id: int,
        message_type: str,
        message: str,
    ) -> int:
        if app_id <= 0 or user_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid app id or user id")
        clean_message = (message or "").strip()
        if not clean_message:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Message is empty")
        normalized_type = self._normalize_message_type(message_type)

        now = datetime.now(UTC)
        record = ChatHistory(
            app_id=app_id,
            user_id=user_id,
            message_type=normalized_type,
            message=clean_message,
            create_time=now,
            update_time=now,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record.id

    async def list_app_chat_history(
        self,
        db: AsyncSession,
        *,
        app_id: int,
        page_size: int,
        last_create_time: datetime | None,
        login_user: User,
    ) -> PageChatHistory:
        app_entity = await db.scalar(select(App).where(App.id == app_id, App.is_delete == 0).limit(1))
        if app_entity is None:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "App not found")
        if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

        page_size = min(max(page_size, 1), 50)
        filters = [ChatHistory.app_id == app_id, ChatHistory.is_delete == 0]
        if last_create_time is not None:
            filters.append(ChatHistory.create_time < last_create_time)

        query_stmt = (
            select(ChatHistory)
            .where(*filters)
            .order_by(desc(ChatHistory.create_time), desc(ChatHistory.id))
            .limit(page_size)
        )
        count_stmt = select(func.count(ChatHistory.id)).where(*filters)
        records = (await db.scalars(query_stmt)).all()
        total_row = int(await db.scalar(count_stmt) or 0)
        total_page = ceil(total_row / page_size) if total_row > 0 else 0

        return PageChatHistory(
            records=[self._to_chat_history_vo(item) for item in records],
            page_number=1,
            page_size=page_size,
            total_page=total_page,
            total_row=total_row,
            optimize_count_query=True,
        )

    async def list_chat_history_by_page_for_admin(
        self, db: AsyncSession, payload: ChatHistoryQueryRequest
    ) -> PageChatHistory:
        page_num = payload.page_num or 1
        page_size = payload.page_size or 10
        if page_num <= 0:
            page_num = 1
        if page_size <= 0:
            page_size = 10
        page_size = min(page_size, 100)

        filters = [ChatHistory.is_delete == 0]
        if payload.id and payload.id > 0:
            filters.append(ChatHistory.id == payload.id)
        if payload.message:
            filters.append(ChatHistory.message.like(f"%{payload.message.strip()}%"))
        if payload.message_type:
            filters.append(ChatHistory.message_type == self._normalize_message_type(payload.message_type))
        if payload.app_id and payload.app_id > 0:
            filters.append(ChatHistory.app_id == payload.app_id)
        if payload.user_id and payload.user_id > 0:
            filters.append(ChatHistory.user_id == payload.user_id)
        if payload.last_create_time:
            filters.append(ChatHistory.create_time < payload.last_create_time)

        query_stmt = select(ChatHistory).where(*filters)
        count_stmt = select(func.count(ChatHistory.id)).where(*filters)
        sort_column = self._sortable_fields.get(payload.sort_field or "")
        sort_order = (payload.sort_order or "").lower()
        if sort_column is not None:
            order_by = desc(sort_column) if "desc" in sort_order else asc(sort_column)
            query_stmt = query_stmt.order_by(order_by)
        else:
            query_stmt = query_stmt.order_by(desc(ChatHistory.create_time), desc(ChatHistory.id))

        offset = (page_num - 1) * page_size
        records = (await db.scalars(query_stmt.offset(offset).limit(page_size))).all()
        total_row = int(await db.scalar(count_stmt) or 0)
        total_page = ceil(total_row / page_size) if total_row > 0 else 0
        return PageChatHistory(
            records=[self._to_chat_history_vo(item) for item in records],
            page_number=page_num,
            page_size=page_size,
            total_page=total_page,
            total_row=total_row,
            optimize_count_query=True,
        )

    @classmethod
    def _normalize_message_type(cls, message_type: str) -> str:
        value = (message_type or "").strip().lower()
        if value == "ai":
            value = MESSAGE_TYPE_ASSISTANT
        if value not in cls._valid_message_types:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid message type")
        return value

    @staticmethod
    def _to_chat_history_vo(entity: ChatHistory) -> ChatHistoryVO:
        return ChatHistoryVO(
            id=entity.id,
            message=entity.message,
            message_type=entity.message_type,
            app_id=entity.app_id,
            user_id=entity.user_id,
            create_time=entity.create_time,
            update_time=entity.update_time,
            is_delete=entity.is_delete,
        )
