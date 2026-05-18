import asyncio
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.ai_codegen_facade import AiCodeGeneratorFacade
from app.core.code_file_saver import CodeFileSaverExecutor
from app.core.code_file_saver import save_html_code
from app.core.code_parser import CodeParserExecutor
from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.sse import build_sse_data, build_sse_event
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


def test_app_add_and_get_vo() -> None:
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        account = f"app_owner_{_unique_suffix()}"
        _register_and_login(client, account=account, password="Pass12345")

        add_resp = client.post("/api/app/add", json={"initPrompt": "生成一个博客首页"})
        add_body = add_resp.json()
        assert add_resp.status_code == 200
        assert add_body["code"] == int(ErrorCode.SUCCESS)
        app_id = add_body["data"]
        assert isinstance(app_id, int)

        get_resp = client.get("/api/app/get/vo", params={"id": app_id})
        get_body = get_resp.json()
        assert get_resp.status_code == 200
        assert get_body["code"] == int(ErrorCode.SUCCESS)
        assert get_body["data"]["id"] == app_id
        assert get_body["data"]["codeGenType"] == "html"


def test_codegen_facade_save_html_file() -> None:
    settings = get_settings()
    original_generated_code_dir = settings.generated_code_dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        settings.generated_code_dir = tmp_dir

        try:
            class FakeAiService:
                async def generate_stream(self, system_prompt: str, user_prompt: str):
                    assert system_prompt
                    assert user_prompt
                    yield "```html\n<html><body><h1>Hello</h1></body></html>\n```"

            facade = AiCodeGeneratorFacade(settings)
            facade.ai_service = FakeAiService()  # type: ignore[assignment]

            async def _run() -> list[str | dict]:
                chunks: list[str | dict] = []
                async for item in facade.generate_and_save_code_stream(
                    app_id=123,
                    user_message="生成一个标题",
                    code_gen_type="html",
                    edit_mode="full",
                ):
                    chunks.append(item)
                return chunks

            chunks = asyncio.run(_run())
            text_chunks = [item for item in chunks if isinstance(item, str)]
            assert len(text_chunks) == 1
            assert any(isinstance(item, dict) and item.get("type") == "tool" for item in chunks)

            output_file = Path(tmp_dir) / "html_123" / "index.html"
            assert output_file.exists()
            assert "<h1>Hello</h1>" in output_file.read_text(encoding="utf-8")
        finally:
            settings.generated_code_dir = original_generated_code_dir


def test_chat_gen_code_sse() -> None:
    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        account = f"app_owner_{_unique_suffix()}"
        _register_and_login(client, account=account, password="Pass12345")

        add_resp = client.post("/api/app/add", json={"initPrompt": "生成一个登陆页"})
        app_id = add_resp.json()["data"]

        class FakeFacade:
            async def generate_and_save_code_stream(
                self,
                app_id: int,
                user_message: str,
                code_gen_type: str,
                edit_mode: str,
            ):
                save_html_code(
                    app_id=app_id,
                    html_code="<html><body>ok</body></html>",
                    settings=get_settings(),
                )
                yield "```html"
                yield "<html><body>ok</body></html>"
                yield "```"

        app.dependency_overrides[get_ai_codegen_facade] = lambda: FakeFacade()
        try:
            with client.stream(
                "GET",
                "/api/app/chat/gen/code",
                params={"appId": app_id, "message": "做一个简洁页面"},
            ) as resp:
                assert resp.status_code == 200
                text = "".join(resp.iter_text())
                assert "event: done" in text
                assert '"d"' in text
        finally:
            app.dependency_overrides.pop(get_ai_codegen_facade, None)


def test_parser_and_saver_executor_for_multi_file() -> None:
    settings = get_settings()
    parser_executor = CodeParserExecutor()
    saver_executor = CodeFileSaverExecutor()
    original_generated_code_dir = settings.generated_code_dir

    raw = "```txt\n# project skeleton\n- app.py\n```"
    parsed = parser_executor.parse(code_gen_type="multi_file", raw_text=raw)
    assert "project skeleton" in parsed

    with tempfile.TemporaryDirectory() as tmp_dir:
        settings.generated_code_dir = tmp_dir
        try:
            output_dir = saver_executor.save(
                code_gen_type="multi_file",
                app_id=88,
                parsed_code=parsed,
                settings=settings,
            )
            output_file = output_dir / "README.md"
            assert output_file.exists()
            assert "project skeleton" in output_file.read_text(encoding="utf-8")
        finally:
            settings.generated_code_dir = original_generated_code_dir


def test_sse_helpers() -> None:
    assert build_sse_data({"d": "x"}) == 'data: {"d": "x"}\n\n'
    assert build_sse_event("done", "done") == "event: done\ndata: done\n\n"
