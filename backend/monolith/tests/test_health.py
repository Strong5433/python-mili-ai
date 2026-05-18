from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.main import app


def test_health_check() -> None:
    client = TestClient(app)
    response = client.get("/api/health/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["message"] == "ok"
    assert payload["data"]["status"] == "UP"
    assert payload["data"]["appName"] == "python-ai-mother-backend"
    assert "timestamp" in payload["data"]
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers


def test_health_validation_error() -> None:
    client = TestClient(app)
    response = client.get("/api/health/?ping=bad")
    payload = response.json()

    assert response.status_code == 200
    assert payload["code"] == int(ErrorCode.PARAMS_ERROR)


def test_business_exception_handler() -> None:
    router = APIRouter(prefix="/api/test", tags=["test"])

    @router.get("/business-error")
    def raise_business_error():
        raise BusinessException(ErrorCode.PARAMS_ERROR, "业务异常测试")

    app.include_router(router)
    client = TestClient(app)
    response = client.get("/api/test/business-error")
    payload = response.json()

    assert response.status_code == 200
    assert payload["code"] == int(ErrorCode.PARAMS_ERROR)
    assert payload["message"] == "业务异常测试"

def test_metrics_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "python_ai_mother_http_requests_total" in response.text
    assert "python_ai_mother_http_request_duration_seconds" in response.text
