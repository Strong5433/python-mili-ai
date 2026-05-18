import io
import sqlite3
import zipfile
from pathlib import Path
from uuid import uuid4

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


def _register_and_login(client: TestClient, account: str, password: str) -> None:
    client.post(
        "/api/user/register",
        json={"userAccount": account, "userPassword": password, "checkPassword": password},
    )
    resp = client.post("/api/user/login", json={"userAccount": account, "userPassword": password})
    assert resp.status_code == 200
    assert resp.json()["code"] == int(ErrorCode.SUCCESS)


def _create_app(client: TestClient, prompt: str) -> int:
    resp = client.post("/api/app/add", json={"initPrompt": prompt})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == int(ErrorCode.SUCCESS)
    return int(body["data"])


def test_app_update_delete_and_my_list() -> None:
    suffix = _unique_suffix()
    account = f"app_user_{suffix}"
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=account, password="Pass12345")
        app_id = _create_app(client, prompt=f"m03_{suffix}_home_page")

        update_resp = client.post("/api/app/update", json={"id": app_id, "appName": f"renamed_{suffix}"})
        assert update_resp.status_code == 200
        assert update_resp.json()["code"] == int(ErrorCode.SUCCESS)

        get_resp = client.get("/api/app/get/vo", params={"id": app_id})
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["appName"] == f"renamed_{suffix}"

        list_resp = client.post(
            "/api/app/my/list/page/vo",
            json={"pageNum": 1, "pageSize": 20, "sortField": "createTime", "sortOrder": "desc"},
        )
        list_body = list_resp.json()
        assert list_resp.status_code == 200
        assert list_body["code"] == int(ErrorCode.SUCCESS)
        records = list_body["data"]["records"]
        assert any(item["id"] == app_id for item in records)

        del_resp = client.post("/api/app/delete", json={"id": app_id})
        assert del_resp.status_code == 200
        assert del_resp.json()["code"] == int(ErrorCode.SUCCESS)

        after_del = client.get("/api/app/get/vo", params={"id": app_id})
        assert after_del.status_code == 200
        assert after_del.json()["code"] == int(ErrorCode.NOT_FOUND_ERROR)


def test_app_admin_list_update_delete_and_good_list() -> None:
    suffix = _unique_suffix()
    user_account = f"app_owner_{suffix}"
    admin_account = f"admin_{suffix}"
    admin_password = "adminPass123"
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=user_account, password="Pass12345")
        app_id = _create_app(client, prompt=f"m03_admin_{suffix}")

        _seed_admin_user(admin_account, admin_password)
        _register_and_login(client, account=admin_account, password=admin_password)

        list_resp = client.post(
            "/api/app/admin/list/page/vo",
            json={"pageNum": 1, "pageSize": 20, "userId": 0},
        )
        list_body = list_resp.json()
        assert list_resp.status_code == 200
        assert list_body["code"] == int(ErrorCode.SUCCESS)
        assert any(item["id"] == app_id for item in list_body["data"]["records"])

        upd_resp = client.post(
            "/api/app/admin/update",
            json={"id": app_id, "priority": 99, "cover": f"https://example.com/{suffix}.png"},
        )
        assert upd_resp.status_code == 200
        assert upd_resp.json()["code"] == int(ErrorCode.SUCCESS)

        good_resp = client.post(
            "/api/app/good/list/page/vo",
            json={"pageNum": 1, "pageSize": 20, "sortField": "createTime", "sortOrder": "desc"},
        )
        good_body = good_resp.json()
        assert good_resp.status_code == 200
        assert good_body["code"] == int(ErrorCode.SUCCESS)
        assert any(item["id"] == app_id for item in good_body["data"]["records"])

        admin_get = client.get("/api/app/admin/get/vo", params={"id": app_id})
        assert admin_get.status_code == 200
        assert admin_get.json()["code"] == int(ErrorCode.SUCCESS)

        del_resp = client.post("/api/app/admin/delete", json={"id": app_id})
        assert del_resp.status_code == 200
        assert del_resp.json()["code"] == int(ErrorCode.SUCCESS)


def test_app_deploy_and_download() -> None:
    suffix = _unique_suffix()
    account = f"deploy_user_{suffix}"
    settings = get_settings()
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=account, password="Pass12345")
        app_id = _create_app(client, prompt=f"m03_deploy_{suffix}")

        source_dir = settings.generated_code_path() / f"html_{app_id}"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "index.html").write_text("<html><body>deploy</body></html>", encoding="utf-8")
        (source_dir / "style.css").write_text("body{color:#333;}", encoding="utf-8")

        deploy_resp = client.post("/api/app/deploy", json={"appId": app_id})
        deploy_body = deploy_resp.json()
        assert deploy_resp.status_code == 200
        assert deploy_body["code"] == int(ErrorCode.SUCCESS)
        assert f"/html_{app_id}/" in deploy_body["data"]

        get_resp = client.get("/api/app/get/vo", params={"id": app_id})
        get_body = get_resp.json()
        assert get_resp.status_code == 200
        assert get_body["code"] == int(ErrorCode.SUCCESS)
        assert get_body["data"]["deployKey"] == f"html_{app_id}"

        static_resp = client.get(f"/api/static/html_{app_id}/")
        assert static_resp.status_code == 200
        assert "<html" in static_resp.text.lower()

        down_resp = client.get(f"/api/app/download/{app_id}")
        assert down_resp.status_code == 200
        assert "application/zip" in down_resp.headers.get("content-type", "")
        assert f'filename="{app_id}.zip"' in down_resp.headers.get("content-disposition", "")

        zip_data = io.BytesIO(down_resp.content)
        with zipfile.ZipFile(zip_data) as zip_file:
            names = set(zip_file.namelist())
            assert "index.html" in names
            assert "style.css" in names
