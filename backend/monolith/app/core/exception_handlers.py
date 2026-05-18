import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.core.response import error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_exception(_: Request, exc: BusinessException) -> JSONResponse:
        payload = error_response(exc.code, exc.message).model_dump()
        return JSONResponse(status_code=200, content=payload)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = error_response(ErrorCode.PARAMS_ERROR, "请求参数错误", exc.errors()).model_dump()
        return JSONResponse(status_code=200, content=payload)

    @app.exception_handler(Exception)
    async def handle_unknown_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error: %s", exc)
        payload = error_response(ErrorCode.SYSTEM_ERROR, "系统内部错误").model_dump()
        return JSONResponse(status_code=200, content=payload)
