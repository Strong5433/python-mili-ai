import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
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


def _register_and_login(client: TestClient, account: str, password: str) -> None:
    client.post(
        "/api/user/register",
        json={"userAccount": account, "userPassword": password, "checkPassword": password},
    )
    login_resp = client.post("/api/user/login", json={"userAccount": account, "userPassword": password})
    assert login_resp.status_code == 200
    assert login_resp.json()["code"] == int(ErrorCode.SUCCESS)


def _create_app(client: TestClient, prompt: str) -> int:
    resp = client.post(
        "/api/app/add",
        json={"initPrompt": prompt, "codeGenType": "html"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == int(ErrorCode.SUCCESS)
    return int(body["data"])


def test_app_version_snapshot_and_rollback() -> None:
    suffix = _unique_suffix()
    settings = get_settings()

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m07_owner_{suffix}", password="Pass12345")

        app_id = _create_app(client, prompt=f"m07_{suffix}")

        source_dir = settings.generated_code_path() / f"html_{app_id}"
        source_dir.mkdir(parents=True, exist_ok=True)
        target_file = source_dir / "index.html"

        target_file.write_text("<html><body>V1</body></html>", encoding="utf-8")
        snap1 = client.post(
            "/api/app/version/snapshot",
            json={"appId": app_id, "message": "first", "editMode": "full"},
        )
        assert snap1.status_code == 200
        assert snap1.json()["code"] == int(ErrorCode.SUCCESS)
        assert snap1.json()["data"]["version"] == 1

        target_file.write_text("<html><body>V2</body></html>", encoding="utf-8")
        snap2 = client.post(
            "/api/app/version/snapshot",
            json={"appId": app_id, "message": "second", "editMode": "incremental"},
        )
        assert snap2.status_code == 200
        assert snap2.json()["code"] == int(ErrorCode.SUCCESS)
        assert snap2.json()["data"]["version"] == 2

        list_resp = client.get("/api/app/version/list", params={"appId": app_id})
        list_body = list_resp.json()
        assert list_resp.status_code == 200
        assert list_body["code"] == int(ErrorCode.SUCCESS)
        assert len(list_body["data"]) >= 2

        rollback_resp = client.post(
            "/api/app/version/rollback",
            json={"appId": app_id, "version": 1},
        )
        rollback_body = rollback_resp.json()
        assert rollback_resp.status_code == 200
        assert rollback_body["code"] == int(ErrorCode.SUCCESS)
        assert rollback_body["data"] is True

        assert "V1" in target_file.read_text(encoding="utf-8")

        index_path = source_dir / ".versions" / "index.json"
        assert index_path.exists()
        items = json.loads(index_path.read_text(encoding="utf-8"))
        assert len(items) >= 2


def test_chat_gen_code_accepts_edit_mode() -> None:
    suffix = _unique_suffix()

    class FakeFacade:
        async def generate_and_save_code_stream(
            self,
            app_id: int,
            user_message: str,
            code_gen_type: str,
            edit_mode: str,
        ):
            assert edit_mode in {"full", "incremental"}
            yield "```html"
            yield "<html><body>M07</body></html>"
            yield "```"

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m07_chat_{suffix}", password="Pass12345")
        app_id = _create_app(client, prompt="m07 chat")

        from app.dependencies import get_ai_codegen_facade

        app.dependency_overrides[get_ai_codegen_facade] = lambda: FakeFacade()
        try:
            with client.stream(
                "GET",
                "/api/app/chat/gen/code",
                params={"appId": app_id, "message": "修改内容", "editMode": "incremental"},
            ) as resp:
                assert resp.status_code == 200
                text = "".join(resp.iter_text())
                assert "event: done" in text
        finally:
            app.dependency_overrides.pop(get_ai_codegen_facade, None)
