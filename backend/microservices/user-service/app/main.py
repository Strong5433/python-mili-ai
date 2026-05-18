from datetime import UTC, datetime
from threading import Lock

from fastapi import FastAPI, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field


SESSION_COOKIE_NAME = "python_ai_mother_sid"
_LOCK = Lock()
_NEXT_USER_ID = 1
_USERS: dict[str, dict] = {}
_SESSIONS: dict[str, str] = {}


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


app = FastAPI(title="python-ai-mother-user-service", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return success({"status": "UP", "service": "user-service"})


@app.post("/api/user/register")
async def register(payload: UserRegisterRequest) -> dict:
    account = payload.user_account.strip()
    password = payload.user_password
    if not account or len(password) < 6:
        return fail(40000, "Invalid register params")
    if payload.user_password != payload.check_password:
        return fail(40000, "Password mismatch")
    with _LOCK:
        global _NEXT_USER_ID
        if account in _USERS:
            return fail(40000, "Account already exists")
        user = {
            "id": _NEXT_USER_ID,
            "userAccount": account,
            "userPassword": password,
            "userRole": "user",
            "createTime": datetime.now(UTC).isoformat(),
        }
        _USERS[account] = user
        _NEXT_USER_ID += 1
    return success(True)


@app.post("/api/user/login")
async def login(payload: UserLoginRequest, response: Response) -> dict:
    account = payload.user_account.strip()
    user = _USERS.get(account)
    if user is None or user.get("userPassword") != payload.user_password:
        return fail(40100, "Invalid account or password")
    session_id = f"sid-{user['id']}-{int(datetime.now(UTC).timestamp())}"
    with _LOCK:
        _SESSIONS[session_id] = account
    response.set_cookie(key=SESSION_COOKIE_NAME, value=session_id, httponly=True)
    data = {k: v for k, v in user.items() if k != "userPassword"}
    data["sessionId"] = session_id
    return success(data)


@app.get("/api/user/get/login")
async def get_login(request: Request) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    account = _SESSIONS.get(session_id or "")
    if not account:
        return fail(40100, "Not login")
    user = _USERS.get(account)
    if not user:
        return fail(40100, "Not login")
    return success({k: v for k, v in user.items() if k != "userPassword"})


@app.post("/api/user/logout")
async def logout(request: Request, response: Response) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        with _LOCK:
            _SESSIONS.pop(session_id, None)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return success(True)


@app.get("/internal/session/validate")
async def validate_session(session_id: str = Query(alias="sessionId")) -> dict:
    account = _SESSIONS.get(session_id)
    if not account:
        return fail(40100, "Not login")
    user = _USERS.get(account)
    if not user:
        return fail(40100, "Not login")
    return success({k: v for k, v in user.items() if k != "userPassword"})


@app.get("/internal/session/delete")
async def delete_session(session_id: str = Query(alias="sessionId")) -> dict:
    with _LOCK:
        _SESSIONS.pop(session_id, None)
    return success(True)
