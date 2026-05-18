from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserVO


class AppAddRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    init_prompt: str | None = Field(default=None, alias="initPrompt")
    code_gen_type: str | None = Field(default=None, alias="codeGenType")
    enable_auto_route: bool = Field(default=True, alias="enableAutoRoute")


class AppUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int | None = None
    app_name: str | None = Field(default=None, alias="appName")


class AppAdminUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int | None = None
    app_name: str | None = Field(default=None, alias="appName")
    cover: str | None = None
    priority: int | None = None
    code_gen_type: str | None = Field(default=None, alias="codeGenType")


class AppDeployRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int | None = Field(default=None, alias="appId")


class AppScreenshotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int | None = Field(default=None, alias="appId")


class AppRouteCodeGenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str
    preferred_code_gen_type: str | None = Field(default=None, alias="preferredCodeGenType")


class AppRouteCodeGenResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_gen_type: str = Field(alias="codeGenType")
    reason: str
    source: str


class AppVersionSnapshotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int | None = Field(default=None, alias="appId")
    message: str | None = None
    edit_mode: str = Field(default="full", alias="editMode")


class AppVersionRollbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int | None = Field(default=None, alias="appId")
    version: int


class AppVersionVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    version: int
    file_name: str = Field(alias="fileName")
    message: str | None = None
    edit_mode: str = Field(alias="editMode")
    created_time: str = Field(alias="createdTime")


class AppQueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page_num: int | None = Field(default=1, alias="pageNum")
    page_size: int | None = Field(default=10, alias="pageSize")
    sort_field: str | None = Field(default=None, alias="sortField")
    sort_order: str | None = Field(default=None, alias="sortOrder")
    id: int | None = None
    app_name: str | None = Field(default=None, alias="appName")
    cover: str | None = None
    init_prompt: str | None = Field(default=None, alias="initPrompt")
    code_gen_type: str | None = Field(default=None, alias="codeGenType")
    deploy_key: str | None = Field(default=None, alias="deployKey")
    priority: int | None = None
    user_id: int | None = Field(default=None, alias="userId")


class AppVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    app_name: str = Field(alias="appName")
    cover: str | None = None
    init_prompt: str | None = Field(default=None, alias="initPrompt")
    code_gen_type: str = Field(alias="codeGenType")
    deploy_key: str | None = Field(default=None, alias="deployKey")
    deployed_time: datetime | None = Field(default=None, alias="deployedTime")
    priority: int = 0
    user_id: int = Field(alias="userId")
    create_time: datetime | None = Field(default=None, alias="createTime")
    update_time: datetime | None = Field(default=None, alias="updateTime")
    user: UserVO | None = None


class PageAppVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    records: list[AppVO]
    page_number: int = Field(alias="pageNumber")
    page_size: int = Field(alias="pageSize")
    total_page: int = Field(alias="totalPage")
    total_row: int = Field(alias="totalRow")
    optimize_count_query: bool = Field(default=True, alias="optimizeCountQuery")


class ChatToGenCodeParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int = Field(alias="appId")
    message: str
