from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
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


def test_add_app_with_vue_project_mode() -> None:
    suffix = _unique_suffix()
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m05_user_{suffix}", password="Pass12345")

        add_resp = client.post(
            "/api/app/add",
            json={"initPrompt": "创建一个任务管理项目", "codeGenType": "vue_project"},
        )
        add_body = add_resp.json()
        assert add_resp.status_code == 200
        assert add_body["code"] == int(ErrorCode.SUCCESS)
        app_id = int(add_body["data"])

        get_resp = client.get("/api/app/get/vo", params={"id": app_id})
        get_body = get_resp.json()
        assert get_resp.status_code == 200
        assert get_body["code"] == int(ErrorCode.SUCCESS)
        assert get_body["data"]["codeGenType"] == "vue_project"


def test_vue_project_chat_stream_with_tool_events_and_deploy() -> None:
    suffix = _unique_suffix()
    settings = get_settings()

    class FakeProjectFacade:
        async def generate_and_save_code_stream(
            self,
            app_id: int,
            user_message: str,
            code_gen_type: str,
            edit_mode: str,
        ):
            output_dir = settings.generated_code_path() / f"{code_gen_type}_{app_id}"
            (output_dir / "dist").mkdir(parents=True, exist_ok=True)
            (output_dir / "dist" / "index.html").write_text(
                "<html><body><h1>M05 Project</h1></body></html>",
                encoding="utf-8",
            )
            (output_dir / "package.json").write_text('{"name":"m05-project"}', encoding="utf-8")

            yield {"type": "tool", "event": "start", "tool": "write.files", "message": "开始写入工程文件"}
            yield "```file:package.json\n{\"name\":\"m05-project\"}\n```"
            yield {"type": "tool", "event": "delta", "tool": "write.files", "message": "已写入 package.json"}
            yield {"type": "tool", "event": "end", "tool": "write.files", "message": "文件写入完成"}

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m05_owner_{suffix}", password="Pass12345")

        add_resp = client.post(
            "/api/app/add",
            json={"initPrompt": "生成一个项目管理工具", "codeGenType": "vue_project"},
        )
        app_id = int(add_resp.json()["data"])

        app.dependency_overrides[get_ai_codegen_facade] = lambda: FakeProjectFacade()
        try:
            with client.stream(
                "GET",
                "/api/app/chat/gen/code",
                params={"appId": app_id, "message": "生成项目"},
            ) as stream_resp:
                assert stream_resp.status_code == 200
                text = "".join(stream_resp.iter_text())
                assert '"type": "tool"' in text
                assert "write.files" in text
                assert "event: done" in text
        finally:
            app.dependency_overrides.pop(get_ai_codegen_facade, None)

        deploy_resp = client.post("/api/app/deploy", json={"appId": app_id})
        deploy_body = deploy_resp.json()
        assert deploy_resp.status_code == 200
        assert deploy_body["code"] == int(ErrorCode.SUCCESS)
        assert f"/vue_project_{app_id}/" in deploy_body["data"]

        static_resp = client.get(f"/api/static/vue_project_{app_id}/dist/index.html")
        assert static_resp.status_code == 200
        assert "M05 Project" in static_resp.text

        generated_dir = Path(settings.generated_code_path()) / f"vue_project_{app_id}"
        assert (generated_dir / "package.json").exists()
