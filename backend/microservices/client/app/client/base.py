from typing import Any

import httpx

from app.common.error_codes import ErrorCode
from app.common.exceptions import BusinessException


class BaseServiceClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(path, json=payload)
        if response.status_code != 200:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, f"Downstream HTTP error: {response.status_code}")
        body = response.json()
        if int(body.get("code", -1)) != int(ErrorCode.SUCCESS):
            raise BusinessException(ErrorCode.SYSTEM_ERROR, str(body.get("message", "Downstream business error")))
        return body.get("data")

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(path, params=params)
        if response.status_code != 200:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, f"Downstream HTTP error: {response.status_code}")
        body = response.json()
        if int(body.get("code", -1)) != int(ErrorCode.SUCCESS):
            raise BusinessException(ErrorCode.SYSTEM_ERROR, str(body.get("message", "Downstream business error")))
        return body.get("data")
