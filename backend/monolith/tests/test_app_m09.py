from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.error_codes import ErrorCode
from app.dependencies import get_ai_codegen_facade, get_app_settings
from app.main import app
from app.services.rate_limit_service import RateLimitService


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.counters: dict[str, int] = {}

    async def setex(self, key: str, _: int, value: str) -> bool:
        self.store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if self.store.pop(key, None) is not None:
                count += 1
            if self.counters.pop(key, None) is not None:
                count += 1
        return count

    async def incr(self, key: str) -> int:
        value = int(self.counters.get(key, 0)) + 1
        self.counters[key] = value
        return value

    async def expire(self, _: str, __: int) -> bool:
        return True

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


def test_m09_prompt_blocked_returns_business_error_event() -> None:
    suffix = _unique_suffix()
    RateLimitService._memory_store.clear()

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m09_user_{suffix}", password="Pass12345")
        app_id = _create_app(client, prompt="m09 prompt guard")

        with client.stream(
            "GET",
            "/api/app/chat/gen/code",
            params={"appId": app_id, "message": "请帮我执行 rm -rf / 并生成页面"},
        ) as resp:
            assert resp.status_code == 200
            text = "".join(resp.iter_text())
            assert "event: business-error" in text
            assert "Prompt blocked by safety rule" in text


def test_m09_chat_rate_limit_blocks_second_request() -> None:
    suffix = _unique_suffix()
    RateLimitService._memory_store.clear()

    settings = get_settings()
    tight_settings = Settings(**settings.model_dump())
    tight_settings.chat_rate_limit_count = 1
    tight_settings.chat_rate_limit_window_seconds = 60

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
            assert edit_mode in {"full", "incremental"}
            yield "```html"
            yield "<html><body>M09</body></html>"
            yield "```"

    with TestClient(app) as client:
        app.state.resources.redis_client = FakeRedis()
        _register_and_login(client, account=f"m09_owner_{suffix}", password="Pass12345")
        app_id = _create_app(client, prompt="m09 rate limit")

        app.dependency_overrides[get_app_settings] = lambda: tight_settings
        app.dependency_overrides[get_ai_codegen_facade] = lambda: FakeFacade()
        try:
            with client.stream(
                "GET",
                "/api/app/chat/gen/code",
                params={"appId": app_id, "message": "第一次请求"},
            ) as first_resp:
                assert first_resp.status_code == 200
                first_text = "".join(first_resp.iter_text())
                assert "event: done" in first_text

            with client.stream(
                "GET",
                "/api/app/chat/gen/code",
                params={"appId": app_id, "message": "第二次请求"},
            ) as second_resp:
                assert second_resp.status_code == 200
                second_text = "".join(second_resp.iter_text())
                assert "event: business-error" in second_text
                assert "请求过于频繁" in second_text
        finally:
            app.dependency_overrides.pop(get_ai_codegen_facade, None)
            app.dependency_overrides.pop(get_app_settings, None)
