from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatHistoryQueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page_num: int | None = Field(default=1, alias="pageNum")
    page_size: int | None = Field(default=10, alias="pageSize")
    sort_field: str | None = Field(default=None, alias="sortField")
    sort_order: str | None = Field(default=None, alias="sortOrder")
    id: int | None = None
    message: str | None = None
    message_type: str | None = Field(default=None, alias="messageType")
    app_id: int | None = Field(default=None, alias="appId")
    user_id: int | None = Field(default=None, alias="userId")
    last_create_time: datetime | None = Field(default=None, alias="lastCreateTime")


class ChatHistoryVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    message: str
    message_type: str = Field(alias="messageType")
    app_id: int = Field(alias="appId")
    user_id: int = Field(alias="userId")
    create_time: datetime | None = Field(default=None, alias="createTime")
    update_time: datetime | None = Field(default=None, alias="updateTime")
    is_delete: int = Field(default=0, alias="isDelete")


class PageChatHistory(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    records: list[ChatHistoryVO]
    page_number: int = Field(alias="pageNumber")
    page_size: int = Field(alias="pageSize")
    total_page: int = Field(alias="totalPage")
    total_row: int = Field(alias="totalRow")
    optimize_count_query: bool = Field(default=True, alias="optimizeCountQuery")
