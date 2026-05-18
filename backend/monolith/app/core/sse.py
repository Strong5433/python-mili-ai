import json
from typing import Any


def build_sse_data(payload: Any) -> str:
    if isinstance(payload, str):
        serialized = payload
    else:
        serialized = json.dumps(payload, ensure_ascii=False)
    return f"data: {serialized}\n\n"


def build_sse_event(event: str, payload: Any) -> str:
    if isinstance(payload, str):
        serialized = payload
    else:
        serialized = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {serialized}\n\n"
