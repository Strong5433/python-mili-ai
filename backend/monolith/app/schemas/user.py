from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str | None = Field(default=None, alias="userAccount")
    user_password: str | None = Field(default=None, alias="userPassword")
    check_password: str | None = Field(default=None, alias="checkPassword")


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str | None = Field(default=None, alias="userAccount")
    user_password: str | None = Field(default=None, alias="userPassword")


class LoginUserVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_account: str = Field(alias="userAccount")
    user_name: str | None = Field(default=None, alias="userName")
    user_avatar: str | None = Field(default=None, alias="userAvatar")
    user_profile: str | None = Field(default=None, alias="userProfile")
    user_role: str = Field(alias="userRole")
    create_time: datetime | None = Field(default=None, alias="createTime")
    update_time: datetime | None = Field(default=None, alias="updateTime")


class DeleteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int | None = None


class UserAddRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_name: str | None = Field(default=None, alias="userName")
    user_account: str | None = Field(default=None, alias="userAccount")
    user_avatar: str | None = Field(default=None, alias="userAvatar")
    user_profile: str | None = Field(default=None, alias="userProfile")
    user_role: str | None = Field(default=None, alias="userRole")


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int | None = None
    user_name: str | None = Field(default=None, alias="userName")
    user_avatar: str | None = Field(default=None, alias="userAvatar")
    user_profile: str | None = Field(default=None, alias="userProfile")
    user_role: str | None = Field(default=None, alias="userRole")


class UserQueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page_num: int | None = Field(default=1, alias="pageNum")
    page_size: int | None = Field(default=10, alias="pageSize")
    sort_field: str | None = Field(default=None, alias="sortField")
    sort_order: str | None = Field(default=None, alias="sortOrder")
    id: int | None = None
    user_name: str | None = Field(default=None, alias="userName")
    user_account: str | None = Field(default=None, alias="userAccount")
    user_profile: str | None = Field(default=None, alias="userProfile")
    user_role: str | None = Field(default=None, alias="userRole")


class UserData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_account: str = Field(alias="userAccount")
    user_password: str = Field(alias="userPassword")
    user_name: str | None = Field(default=None, alias="userName")
    user_avatar: str | None = Field(default=None, alias="userAvatar")
    user_profile: str | None = Field(default=None, alias="userProfile")
    user_role: str = Field(alias="userRole")
    edit_time: datetime | None = Field(default=None, alias="editTime")
    create_time: datetime | None = Field(default=None, alias="createTime")
    update_time: datetime | None = Field(default=None, alias="updateTime")
    is_delete: int = Field(alias="isDelete")


class UserVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_account: str = Field(alias="userAccount")
    user_name: str | None = Field(default=None, alias="userName")
    user_avatar: str | None = Field(default=None, alias="userAvatar")
    user_profile: str | None = Field(default=None, alias="userProfile")
    user_role: str = Field(alias="userRole")
    create_time: datetime | None = Field(default=None, alias="createTime")


class PageUserVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    records: list[UserVO]
    page_number: int = Field(alias="pageNumber")
    page_size: int = Field(alias="pageSize")
    total_page: int = Field(alias="totalPage")
    total_row: int = Field(alias="totalRow")
    optimize_count_query: bool = Field(default=True, alias="optimizeCountQuery")
