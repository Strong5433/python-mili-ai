from typing import Any

from app.common.error_codes import ErrorCode


def success_response(data: Any = None) -> dict[str, Any]:
    return {"code": int(ErrorCode.SUCCESS), "message": "ok", "data": data}


def error_response(code: ErrorCode, message: str) -> dict[str, Any]:
    return {"code": int(code), "message": message, "data": None}
