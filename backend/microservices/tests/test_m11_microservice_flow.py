import importlib.util
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient


BASE_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module: {module_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pick_app(base_url: str, user_module, ai_module, screenshot_module):
    if "8201" in base_url:
        return user_module.app
    if "8202" in base_url:
        return ai_module.app
    if "8204" in base_url:
        return screenshot_module.app
    raise RuntimeError(f"Unsupported base url: {base_url}")


def test_m11_cross_service_smoke(monkeypatch) -> None:
    user_module = _load_module("m11_user_service", BASE_DIR / "user-service" / "app" / "main.py")
    ai_module = _load_module("m11_ai_service", BASE_DIR / "ai-service" / "app" / "main.py")
    screenshot_module = _load_module(
        "m11_screenshot_service",
        BASE_DIR / "screenshot-service" / "app" / "main.py",
    )
    app_module = _load_module("m11_app_service", BASE_DIR / "app-service" / "app" / "main.py")

    async def _fake_call_get(base_url: str, path: str, params=None):
        target_app = _pick_app(base_url, user_module, ai_module, screenshot_module)
        transport = httpx.ASGITransport(app=target_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://service") as client:
            response = await client.get(path, params=params)
        return response.json()

    async def _fake_call_post(base_url: str, path: str, payload: dict):
        target_app = _pick_app(base_url, user_module, ai_module, screenshot_module)
        transport = httpx.ASGITransport(app=target_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://service") as client:
            response = await client.post(path, json=payload)
        return response.json()

    monkeypatch.setattr(app_module, "call_get", _fake_call_get)
    monkeypatch.setattr(app_module, "call_post", _fake_call_post)

    suffix = uuid4().hex[:8]
    with TestClient(app_module.app) as client:
        register_resp = client.post(
            "/api/user/register",
            json={
                "userAccount": f"micro_{suffix}",
                "userPassword": "Pass12345",
                "checkPassword": "Pass12345",
            },
        )
        assert register_resp.status_code == 200
        assert register_resp.json()["code"] == 0

        login_resp = client.post(
            "/api/user/login",
            json={"userAccount": f"micro_{suffix}", "userPassword": "Pass12345"},
        )
        assert login_resp.status_code == 200
        assert login_resp.json()["code"] == 0
        session_cookie = login_resp.cookies.get("python_ai_mother_sid")
        assert session_cookie

        add_resp = client.post(
            "/api/app/add",
            json={"initPrompt": "M11 微服务链路", "codeGenType": "html"},
            cookies={"python_ai_mother_sid": session_cookie},
        )
        assert add_resp.status_code == 200
        assert add_resp.json()["code"] == 0
        app_id = int(add_resp.json()["data"])

        with client.stream(
            "GET",
            "/api/app/chat/gen/code",
            params={"appId": app_id, "message": "生成一个介绍页"},
            cookies={"python_ai_mother_sid": session_cookie},
        ) as stream_resp:
            assert stream_resp.status_code == 200
            text = "".join(stream_resp.iter_text())
            assert "Python AI Mother" in text
            assert "event: done" in text

        get_resp = client.get(
            "/api/app/get/vo",
            params={"id": app_id},
            cookies={"python_ai_mother_sid": session_cookie},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["code"] == 0
        assert "generatedCode" in get_resp.json()["data"]

        shot_resp = client.post(
            "/api/app/screenshot",
            json={"appId": app_id},
            cookies={"python_ai_mother_sid": session_cookie},
        )
        assert shot_resp.status_code == 200
        assert shot_resp.json()["code"] == 0
        assert str(shot_resp.json()["data"]).startswith("/static/screenshots/")
