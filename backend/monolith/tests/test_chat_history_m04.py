import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.security import hash_password
from app.dependencies import get_ai_codegen_facade
from app.main import app


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def setex(self, key: str, _: int, value: str) -> bool:
        self.store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0

    async def aclose(self) -> None:
        return None


class FakeFacade:
    async def generate_and_save_code_stream(
        self,
        app_id: int,
        user_message: str,
        code_gen_type: str,
        edit_mode: str,
    ):
        assert app_id > 0
        assert user_message
        assert code_gen_type
        yield "```html\n"
        yield "<html><body>m04</body></html>\n"
        yield "```"


def _unique_suffix() -> str:
    return uuid4().hex[:8]


def _sqlite_db_path() -> Path:
    settings = get_settings()
    prefix = "sqlite+aiosqlite:///"
    if not settings.database_url.startswith(prefix):
        raise RuntimeError("Tests currently only support sqlite database_url")
    return Path(settings.database_url[len(prefix) :]).resolve()


def _seed_admin_user(account: str, password: str) -> None:
    settings = get_settings()
    hashed_password = hash_password(password, settings.password_salt)
    db_path = _sqlite_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user (user_account, user_password, user_name, user_role, is_delete)
            VALUES (?, ?, ?, ?, 0)
            """,
            (account, hashed_password, "admin", "admin"),
        )
        conn.commit()


def _register_and_login(client: TestClient, account: str, password: str) -> None:
    client.post(
        "/api/user/register",
        json={"userAccount": account, "userPassword": password, "checkPassword": password},
    )
    login_resp = client.post("/api/user/login", json={"userAccount": account, "userPassword": password})
    assert login_resp.status_code == 200
    assert login_resp.json()["code"] == int(ErrorCode.SUCCESS)


def _create_app(client: TestClient, prompt: str) -> int:
    resp = client.post("/api/app/add", json={"initPrompt": prompt})
    assert resp.status_code == 200
    assert resp.json()["code"] == int(ErrorCode.SUCCESS)
    return int(resp.json()["data"])


def _run_chat(client: TestClient, app_id: int, msg: str) -> None:
    with client.stream(
        "GET",
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": msg},
    ) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
        assert "event: done" in text


def test_chat_history_persistence_and_cursor() -> None:
    suffix = _unique_suffix()
    account = f"m04_user_{suffix}"
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        app.dependency_overrides[get_ai_codegen_facade] = lambda: FakeFacade()
        try:
            _register_and_login(client, account, "Pass12345")
            app_id = _create_app(client, f"m04_{suffix}")
            _run_chat(client, app_id, "生成首页")
            _run_chat(client, app_id, "再加一个按钮")

            page_1_resp = client.get(f"/api/chatHistory/app/{app_id}", params={"pageSize": 3})
            page_1_body = page_1_resp.json()
            assert page_1_resp.status_code == 200
            assert page_1_body["code"] == int(ErrorCode.SUCCESS)
            records_1 = page_1_body["data"]["records"]
            assert len(records_1) == 3
            assert records_1[0]["messageType"] in {"user", "assistant"}
            assert records_1[1]["messageType"] in {"user", "assistant"}
            assert records_1[2]["messageType"] in {"user", "assistant"}

            last_create_time = records_1[-1]["createTime"]
            page_2_resp = client.get(
                f"/api/chatHistory/app/{app_id}",
                params={"pageSize": 3, "lastCreateTime": last_create_time},
            )
            page_2_body = page_2_resp.json()
            assert page_2_resp.status_code == 200
            assert page_2_body["code"] == int(ErrorCode.SUCCESS)
            records_2 = page_2_body["data"]["records"]
            assert len(records_2) >= 1
            ids_1 = {item["id"] for item in records_1}
            ids_2 = {item["id"] for item in records_2}
            assert ids_1.isdisjoint(ids_2)
        finally:
            app.dependency_overrides.pop(get_ai_codegen_facade, None)


def test_chat_history_admin_list_requires_admin_role() -> None:
    suffix = _unique_suffix()
    user_account = f"m04_owner_{suffix}"
    admin_account = f"m04_admin_{suffix}"
    admin_password = "adminPass123"
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        app.dependency_overrides[get_ai_codegen_facade] = lambda: FakeFacade()
        try:
            _register_and_login(client, user_account, "Pass12345")
            app_id = _create_app(client, f"m04_admin_{suffix}")
            _run_chat(client, app_id, "hello")

            denied_resp = client.post(
                "/api/chatHistory/admin/list/page/vo",
                json={"pageNum": 1, "pageSize": 10},
            )
            assert denied_resp.status_code == 200
            assert denied_resp.json()["code"] == int(ErrorCode.NO_AUTH_ERROR)

            _seed_admin_user(admin_account, admin_password)
            _register_and_login(client, admin_account, admin_password)

            ok_resp = client.post(
                "/api/chatHistory/admin/list/page/vo",
                json={
                    "pageNum": 1,
                    "pageSize": 10,
                    "appId": app_id,
                    "sortField": "createTime",
                    "sortOrder": "desc",
                },
            )
            ok_body = ok_resp.json()
            assert ok_resp.status_code == 200
            assert ok_body["code"] == int(ErrorCode.SUCCESS)
            assert ok_body["data"]["totalRow"] >= 2
            assert any(item["appId"] == app_id for item in ok_body["data"]["records"])
        finally:
            app.dependency_overrides.pop(get_ai_codegen_facade, None)
