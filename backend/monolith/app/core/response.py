from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from app.core.error_codes import ErrorCode

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None


def success_response(data: Optional[T] = None, message: str = "ok") -> BaseResponse[T]:
    return BaseResponse(code=int(ErrorCode.SUCCESS), message=message, data=data)


def error_response(code: ErrorCode, message: str, data: Optional[T] = None) -> BaseResponse[T]:
    return BaseResponse(code=int(code), message=message, data=data)

