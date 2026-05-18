import json
import os
from datetime import UTC, datetime
from threading import Lock
from typing import Any

import httpx
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field


SESSION_COOKIE_NAME = "python_ai_mother_sid"
USER_SERVICE_BASE_URL = os.getenv("USER_SERVICE_BASE_URL", "http://localhost:8201")
AI_SERVICE_BASE_URL = os.getenv("AI_SERVICE_BASE_URL", "http://localhost:8202")
SCREENSHOT_SERVICE_BASE_URL = os.getenv("SCREENSHOT_SERVICE_BASE_URL", "http://localhost:8204")

_LOCK = Lock()
_NEXT_APP_ID = 1
_APPS: dict[int, dict[str, Any]] = {}


class AppCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    init_prompt: str | None = Field(default=None, alias="initPrompt")
    code_gen_type: str = Field(default="html", alias="codeGenType")


class ScreenshotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int = Field(alias="appId")


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(alias="userAccount")
    user_password: str = Field(alias="userPassword")
    check_password: str = Field(alias="checkPassword")


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(alias="userAccount")
    user_password: str = Field(alias="userPassword")


def success(data=None) -> dict:
    return {"code": 0, "message": "ok", "data": data}


def fail(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}


def sse_data(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def sse_event(event: str, data: Any) -> str:
    body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {body}\n\n"


async def call_get(base_url: str, path: str, params: dict[str, Any] | None = None) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.get(path, params=params)
    return response.json()


async def call_post(base_url: str, path: str, payload: dict[str, Any]) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
        response = await client.post(path, json=payload)
    return response.json()


async def require_login_user(request: Request) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise ValueError("Not login")
    body = await call_get(
        USER_SERVICE_BASE_URL,
        "/internal/session/validate",
        params={"sessionId": session_id},
    )
    if int(body.get("code", -1)) != 0:
        raise ValueError(str(body.get("message", "Not login")))
    return dict(body.get("data") or {})


def to_app_vo(app_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": app_row["id"],
        "appName": app_row["appName"],
        "initPrompt": app_row["initPrompt"],
        "codeGenType": app_row["codeGenType"],
        "userId": app_row["userId"],
        "generatedCode": app_row.get("generatedCode"),
        "createTime": app_row["createTime"],
    }


app = FastAPI(title="python-ai-mother-app-service", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return success({"status": "UP", "service": "app-service"})


@app.post("/api/user/register")
async def user_register(payload: UserRegisterRequest) -> dict:
    body = await call_post(
        USER_SERVICE_BASE_URL,
        "/api/user/register",
        payload=payload.model_dump(by_alias=True),
    )
    return dict(body)


@app.post("/api/user/login")
async def user_login(payload: UserLoginRequest, response: Response) -> dict:
    body = await call_post(
        USER_SERVICE_BASE_URL,
        "/api/user/login",
        payload=payload.model_dump(by_alias=True),
    )
    data = body.get("data") or {}
    session_id = data.get("sessionId")
    if session_id:
        response.set_cookie(key=SESSION_COOKIE_NAME, value=session_id, httponly=True)
    return body


@app.get("/api/user/get/login")
async def user_get_login(request: Request) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return fail(40100, "Not login")
    return await call_get(
        USER_SERVICE_BASE_URL,
        "/internal/session/validate",
        params={"sessionId": session_id},
    )


@app.post("/api/user/logout")
async def user_logout(request: Request, response: Response) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        await call_get(
            USER_SERVICE_BASE_URL,
            "/internal/session/delete",
            params={"sessionId": session_id},
        )
    response.delete_cookie(SESSION_COOKIE_NAME)
    return success(True)


@app.post("/api/app/add")
async def add_app(payload: AppCreateRequest, request: Request) -> dict:
    try:
        login_user = await require_login_user(request)
    except ValueError as exc:
        return fail(40100, str(exc))

    init_prompt = (payload.init_prompt or "").strip() or None
    with _LOCK:
        global _NEXT_APP_ID
        app_id = _NEXT_APP_ID
        _NEXT_APP_ID += 1
        _APPS[app_id] = {
            "id": app_id,
            "appName": (init_prompt or "My App")[:32],
            "initPrompt": init_prompt,
            "codeGenType": payload.code_gen_type,
            "userId": int(login_user.get("id", 0)),
            "generatedCode": None,
            "createTime": datetime.now(UTC).isoformat(),
        }
    return success(app_id)


@app.get("/api/app/get/vo")
async def get_app_vo(request: Request, id: int = Query(gt=0)) -> dict:
    try:
        login_user = await require_login_user(request)
    except ValueError as exc:
        return fail(40100, str(exc))

    app_row = _APPS.get(id)
    if not app_row:
        return fail(40400, "App not found")
    if app_row["userId"] != int(login_user.get("id", -1)):
        return fail(40101, "No permission")
    return success(to_app_vo(app_row))


@app.get("/api/app/chat/gen/code")
async def chat_gen_code(
    request: Request,
    app_id: int = Query(alias="appId", gt=0),
    message: str = Query(min_length=1),
) -> StreamingResponse:
    try:
        login_user = await require_login_user(request)
    except ValueError as exc:
        async def _not_login_stream():
            yield sse_event("business-error", {"code": 40100, "message": str(exc)})
        return StreamingResponse(_not_login_stream(), media_type="text/event-stream")

    app_row = _APPS.get(app_id)
    if app_row is None:
        async def _not_found_stream():
            yield sse_event("business-error", {"code": 40400, "message": "App not found"})
        return StreamingResponse(_not_found_stream(), media_type="text/event-stream")
    if app_row["userId"] != int(login_user.get("id", -1)):
        async def _forbidden_stream():
            yield sse_event("business-error", {"code": 40101, "message": "No permission"})
        return StreamingResponse(_forbidden_stream(), media_type="text/event-stream")

    prompt = message.strip()
    if app_row.get("initPrompt"):
        prompt = f"{app_row['initPrompt']}\n\n{prompt}"

    async def _stream():
        body = await call_post(
            AI_SERVICE_BASE_URL,
            "/internal/ai/generate",
            payload={"prompt": prompt, "codeGenType": app_row["codeGenType"]},
        )
        if int(body.get("code", -1)) != 0:
            yield sse_event("business-error", {"code": 50000, "message": body.get("message", "AI service error")})
            return
        data = body.get("data") or {}
        code = str(data.get("code") or "")
        with _LOCK:
            app_row["generatedCode"] = code
        yield sse_data({"d": code})
        yield sse_event("done", "done")

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(_stream(), media_type="text/event-stream", headers=headers)


@app.post("/api/app/screenshot")
async def capture_screenshot(payload: ScreenshotRequest, request: Request) -> dict:
    try:
        login_user = await require_login_user(request)
    except ValueError as exc:
        return fail(40100, str(exc))

    app_row = _APPS.get(payload.app_id)
    if not app_row:
        return fail(40400, "App not found")
    if app_row["userId"] != int(login_user.get("id", -1)):
        return fail(40101, "No permission")
    html_code = str(app_row.get("generatedCode") or "")
    body = await call_post(
        SCREENSHOT_SERVICE_BASE_URL,
        "/internal/screenshot/capture",
        payload={"appId": app_row["id"], "htmlCode": html_code},
    )
    if int(body.get("code", -1)) != 0:
        return fail(50000, str(body.get("message", "Screenshot service error")))
    return success(body.get("data"))
