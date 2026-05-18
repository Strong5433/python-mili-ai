import io
import zipfile
from pathlib import Path
from urllib.parse import urlparse
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


def _create_app(client: TestClient, init_prompt: str, code_gen_type: str | None = None) -> int:
    payload: dict[str, object] = {"initPrompt": init_prompt}
    if code_gen_type is not None:
        payload["codeGenType"] = code_gen_type
    resp = client.post("/api/app/add", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == int(ErrorCode.SUCCESS)
    return int(body["data"])


def test_route_codegen_type_and_auto_add() -> None:
    suffix = _unique_suffix()
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()

        route_resp = client.post(
            "/api/app/route/codegen",
            json={"prompt": "请生成一个包含组件和路由的 vue3 + vite 项目"},
        )
        route_body = route_resp.json()
        assert route_resp.status_code == 200
        assert route_body["code"] == int(ErrorCode.SUCCESS)
        assert route_body["data"]["codeGenType"] == "vue_project"

        _register_and_login(client, account=f"m06_route_{suffix}", password="Pass12345")
        app_id = _create_app(client, init_prompt="做一个多页面企业官网")

        get_resp = client.get("/api/app/get/vo", params={"id": app_id})
        get_body = get_resp.json()
        assert get_resp.status_code == 200
        assert get_body["code"] == int(ErrorCode.SUCCESS)
        assert get_body["data"]["codeGenType"] in {"html", "multi_file", "vue_project"}


def test_project_download_and_screenshot_flow() -> None:
    suffix = _unique_suffix()
    settings = get_settings()

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m06_owner_{suffix}", password="Pass12345")

        app_id = _create_app(client, init_prompt=f"m06_download_{suffix}", code_gen_type="html")
        source_dir = settings.generated_code_path() / f"html_{app_id}"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "index.html").write_text("<html><body>M06</body></html>", encoding="utf-8")
        (source_dir / "style.css").write_text("body{margin:0}", encoding="utf-8")

        down_resp = client.get(f"/api/app/download/project/{app_id}")
        assert down_resp.status_code == 200
        assert "application/zip" in down_resp.headers.get("content-type", "")

        zip_data = io.BytesIO(down_resp.content)
        with zipfile.ZipFile(zip_data) as zip_file:
            names = set(zip_file.namelist())
            assert any(name.endswith("index.html") for name in names)
            assert any(name.endswith("python-ai-mother-manifest.json") for name in names)

        screenshot_resp = client.post("/api/app/screenshot", json={"appId": app_id})
        screenshot_body = screenshot_resp.json()
        assert screenshot_resp.status_code == 200
        assert screenshot_body["code"] == int(ErrorCode.SUCCESS)

        screenshot_url = str(screenshot_body["data"])
        path = urlparse(screenshot_url).path
        static_resp = client.get(path)
        assert static_resp.status_code == 200
        assert "image/png" in static_resp.headers.get("content-type", "")

        app_get_resp = client.get("/api/app/get/vo", params={"id": app_id})
        app_get_body = app_get_resp.json()
        assert app_get_resp.status_code == 200
        assert app_get_body["code"] == int(ErrorCode.SUCCESS)
        assert app_get_body["data"]["cover"]

        screenshot_dir = Path(settings.generated_code_path()) / f"html_{app_id}" / ".screenshots"
        assert any(item.suffix == ".png" for item in screenshot_dir.glob("*.png"))
