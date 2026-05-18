import threading
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import FastAPI, Request, Response


_DURATION_BUCKETS = (0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0)
_LOCK = threading.Lock()
_REQUEST_TOTAL: dict[tuple[str, str, str], int] = defaultdict(int)
_REQUEST_DURATION_SUM: dict[tuple[str, str], float] = defaultdict(float)
_REQUEST_DURATION_COUNT: dict[tuple[str, str], int] = defaultdict(int)
_REQUEST_DURATION_BUCKET: dict[tuple[str, str, float], int] = defaultdict(int)


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _fmt_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = [f'{key}="{_escape_label(val)}"' for key, val in labels.items()]
    return "{" + ",".join(parts) + "}"


def _observe_duration(method: str, route: str, seconds: float) -> None:
    key = (method, route)
    _REQUEST_DURATION_SUM[key] += seconds
    _REQUEST_DURATION_COUNT[key] += 1
    for boundary in _DURATION_BUCKETS:
        if seconds <= boundary:
            _REQUEST_DURATION_BUCKET[(method, route, boundary)] += 1
    _REQUEST_DURATION_BUCKET[(method, route, float("inf"))] += 1


def _render_metrics() -> str:
    lines: list[str] = []
    lines.append("# HELP python_ai_mother_http_requests_total Total HTTP requests")
    lines.append("# TYPE python_ai_mother_http_requests_total counter")
    for (method, route, status_code), count in sorted(_REQUEST_TOTAL.items()):
        labels = _fmt_labels({"method": method, "route": route, "status_code": status_code})
        lines.append(f"python_ai_mother_http_requests_total{labels} {count}")

    lines.append("# HELP python_ai_mother_http_request_duration_seconds HTTP request duration in seconds")
    lines.append("# TYPE python_ai_mother_http_request_duration_seconds histogram")
    duration_keys = sorted(_REQUEST_DURATION_COUNT.keys())
    for method, route in duration_keys:
        cumulative = 0
        for boundary in _DURATION_BUCKETS:
            cumulative += _REQUEST_DURATION_BUCKET.get((method, route, boundary), 0)
            labels = _fmt_labels({"method": method, "route": route, "le": str(boundary)})
            lines.append(f"python_ai_mother_http_request_duration_seconds_bucket{labels} {cumulative}")
        inf_count = _REQUEST_DURATION_BUCKET.get((method, route, float("inf")), 0)
        labels_inf = _fmt_labels({"method": method, "route": route, "le": "+Inf"})
        lines.append(f"python_ai_mother_http_request_duration_seconds_bucket{labels_inf} {inf_count}")
        labels = _fmt_labels({"method": method, "route": route})
        lines.append(
            f"python_ai_mother_http_request_duration_seconds_sum{labels} {_REQUEST_DURATION_SUM[(method, route)]}"
        )
        lines.append(f"python_ai_mother_http_request_duration_seconds_count{labels} {_REQUEST_DURATION_COUNT[(method, route)]}")
    return "\n".join(lines) + "\n"


def register_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        method = request.method
        route = request.url.path
        status_code = 500

        try:
            response = await call_next(request)
            route_template = request.scope.get("route")
            if route_template is not None and hasattr(route_template, "path"):
                route = str(route_template.path)
            status_code = response.status_code
            return response
        finally:
            elapsed = max(0.0, time.perf_counter() - start)
            with _LOCK:
                _REQUEST_TOTAL[(method, route, str(status_code))] += 1
                _observe_duration(method, route, elapsed)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> Response:
        with _LOCK:
            text = _render_metrics()
        return Response(content=text, media_type="text/plain; version=0.0.4; charset=utf-8")
