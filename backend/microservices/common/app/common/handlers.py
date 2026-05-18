from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.error_codes import ErrorCode
from app.common.exceptions import BusinessException
from app.common.response import error_response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_exception(_: Request, exc: BusinessException) -> JSONResponse:
        return JSONResponse(status_code=200, content=error_response(exc.code, exc.message))

    @app.exception_handler(Exception)
    async def handle_exception(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content=error_response(ErrorCode.SYSTEM_ERROR, f"System error: {exc}"),
        )
