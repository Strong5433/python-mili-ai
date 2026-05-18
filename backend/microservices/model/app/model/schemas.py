from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(alias="userAccount")
    user_password: str = Field(alias="userPassword")
    check_password: str = Field(alias="checkPassword")


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(alias="userAccount")
    user_password: str = Field(alias="userPassword")


class SessionUser(BaseModel):
    id: int
    user_account: str = Field(alias="userAccount")
    user_role: str = Field(alias="userRole")
    create_time: datetime = Field(alias="createTime")


class AppCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    init_prompt: str | None = Field(default=None, alias="initPrompt")
    code_gen_type: str = Field(default="html", alias="codeGenType")


class AppVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    app_name: str = Field(alias="appName")
    init_prompt: str | None = Field(default=None, alias="initPrompt")
    code_gen_type: str = Field(alias="codeGenType")
    user_id: int = Field(alias="userId")
    generated_code: str | None = Field(default=None, alias="generatedCode")
    create_time: datetime = Field(alias="createTime")


class CodeGenRequest(BaseModel):
    prompt: str
    code_gen_type: str = Field(default="html", alias="codeGenType")


class CodeGenResult(BaseModel):
    code: str
    language: str = "html"
