import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.security import hash_password
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


def _login(client: TestClient, account: str, password: str) -> None:
    response = client.post(
        "/api/user/login",
        json={"userAccount": account, "userPassword": password},
    )
    assert response.status_code == 200
    assert response.json()["code"] == int(ErrorCode.SUCCESS)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        app.state.resources.redis_client = FakeRedis()
        yield test_client


def test_user_register_login_logout_flow(client: TestClient) -> None:
    suffix = _unique_suffix()
    account = f"demo_user_{suffix}"
    password = "strongPass123"

    register_payload = {
        "userAccount": account,
        "userPassword": password,
        "checkPassword": password,
    }
    register_response = client.post("/api/user/register", json=register_payload)
    assert register_response.status_code == 200
    register_body = register_response.json()
    assert register_body["code"] == int(ErrorCode.SUCCESS)
    assert isinstance(register_body["data"], int)

    login_response = client.post(
        "/api/user/login",
        json={"userAccount": account, "userPassword": password},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["code"] == int(ErrorCode.SUCCESS)
    assert login_body["data"]["userAccount"] == account
    assert "set-cookie" in login_response.headers

    current_response = client.get("/api/user/get/login")
    assert current_response.status_code == 200
    current_body = current_response.json()
    assert current_body["code"] == int(ErrorCode.SUCCESS)
    assert current_body["data"]["userAccount"] == account

    logout_response = client.post("/api/user/logout")
    assert logout_response.status_code == 200
    logout_body = logout_response.json()
    assert logout_body["code"] == int(ErrorCode.SUCCESS)
    assert logout_body["data"] is True

    after_logout_response = client.get("/api/user/get/login")
    after_logout_body = after_logout_response.json()
    assert after_logout_response.status_code == 200
    assert after_logout_body["code"] == int(ErrorCode.NOT_LOGIN_ERROR)


def test_user_login_with_invalid_password(client: TestClient) -> None:
    suffix = _unique_suffix()
    account = f"another_user_{suffix}"

    client.post(
        "/api/user/register",
        json={
            "userAccount": account,
            "userPassword": "strongPass123",
            "checkPassword": "strongPass123",
        },
    )
    response = client.post(
        "/api/user/login",
        json={"userAccount": account, "userPassword": "wrong_password"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == int(ErrorCode.PARAMS_ERROR)


def test_user_get_login_without_session(client: TestClient) -> None:
    response = client.get("/api/user/get/login")
    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == int(ErrorCode.NOT_LOGIN_ERROR)


def test_admin_crud_and_page_flow(client: TestClient) -> None:
    suffix = _unique_suffix()
    admin_account = f"admin_root_{suffix}"
    managed_account = f"managed_user_{suffix}"
    admin_password = "adminPass123"

    _seed_admin_user(admin_account, admin_password)
    _login(client, admin_account, admin_password)

    add_response = client.post(
        "/api/user/add",
        json={
            "userAccount": managed_account,
            "userName": "Managed User",
            "userRole": "user",
        },
    )
    assert add_response.status_code == 200
    add_payload = add_response.json()
    assert add_payload["code"] == int(ErrorCode.SUCCESS)
    managed_user_id = add_payload["data"]
    assert isinstance(managed_user_id, int)

    get_response = client.get("/api/user/get", params={"id": managed_user_id})
    get_payload = get_response.json()
    assert get_response.status_code == 200
    assert get_payload["code"] == int(ErrorCode.SUCCESS)
    assert get_payload["data"]["userAccount"] == managed_account

    get_vo_response = client.get("/api/user/get/vo", params={"id": managed_user_id})
    get_vo_payload = get_vo_response.json()
    assert get_vo_response.status_code == 200
    assert get_vo_payload["code"] == int(ErrorCode.SUCCESS)
    assert get_vo_payload["data"]["userAccount"] == managed_account

    update_response = client.post(
        "/api/user/update",
        json={"id": managed_user_id, "userName": "Managed User v2", "userRole": "admin"},
    )
    update_payload = update_response.json()
    assert update_response.status_code == 200
    assert update_payload["code"] == int(ErrorCode.SUCCESS)
    assert update_payload["data"] is True

    list_response = client.post(
        "/api/user/list/page/vo",
        json={"pageNum": 1, "pageSize": 10, "userAccount": managed_account},
    )
    list_payload = list_response.json()
    assert list_response.status_code == 200
    assert list_payload["code"] == int(ErrorCode.SUCCESS)
    assert list_payload["data"]["totalRow"] >= 1
    assert len(list_payload["data"]["records"]) >= 1

    delete_response = client.post("/api/user/delete", json={"id": managed_user_id})
    delete_payload = delete_response.json()
    assert delete_response.status_code == 200
    assert delete_payload["code"] == int(ErrorCode.SUCCESS)
    assert delete_payload["data"] is True

    after_delete_response = client.get("/api/user/get", params={"id": managed_user_id})
    after_delete_payload = after_delete_response.json()
    assert after_delete_response.status_code == 200
    assert after_delete_payload["code"] == int(ErrorCode.NOT_FOUND_ERROR)


def test_admin_api_requires_admin_role(client: TestClient) -> None:
    suffix = _unique_suffix()
    account = f"normal_user_{suffix}"
    password = "normalPass123"

    client.post(
        "/api/user/register",
        json={
            "userAccount": account,
            "userPassword": password,
            "checkPassword": password,
        },
    )
    _login(client, account, password)

    response = client.post(
        "/api/user/list/page/vo",
        json={"pageNum": 1, "pageSize": 10},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["code"] == int(ErrorCode.NO_AUTH_ERROR)
