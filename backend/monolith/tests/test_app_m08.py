from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.error_codes import ErrorCode
from app.dependencies import get_codegen_workflow_runner
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


def test_workflow_sse_with_node_trace() -> None:
    suffix = _unique_suffix()

    class FakeWorkflowRunner:
        async def run_stream(self, app_id: int, user_message: str, code_gen_type: str, edit_mode: str):
            assert app_id > 0
            assert user_message
            assert code_gen_type
            assert edit_mode in {"full", "incremental"}
            yield {"type": "workflow", "node": "router", "event": "start", "message": "router start"}
            yield {"type": "workflow", "node": "router", "event": "end", "message": "router end"}
            yield "```html"
            yield "<html><body>M08</body></html>"
            yield "```"

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m08_user_{suffix}", password="Pass12345")
        app_id = _create_app(client, prompt="m08 workflow")

        app.dependency_overrides[get_codegen_workflow_runner] = lambda: FakeWorkflowRunner()
        try:
            with client.stream(
                "GET",
                "/api/app/chat/gen/workflow",
                params={"appId": app_id, "message": "生成页面", "editMode": "full"},
            ) as resp:
                assert resp.status_code == 200
                text = "".join(resp.iter_text())
                assert "workflow" in text
                assert "router" in text
                assert "event: done" in text
        finally:
            app.dependency_overrides.pop(get_codegen_workflow_runner, None)
