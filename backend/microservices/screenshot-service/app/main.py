from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from PIL import Image, ImageDraw


class ScreenshotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: int = Field(alias="appId")
    html_code: str = Field(alias="htmlCode")


def success(data=None) -> dict:
    return {"code": 0, "message": "ok", "data": data}


ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
SCREENSHOT_DIR = ARTIFACT_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="python-ai-mother-screenshot-service", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(ARTIFACT_DIR), html=True), name="static")


@app.get("/health")
async def health() -> dict:
    return success({"status": "UP", "service": "screenshot-service"})


@app.post("/internal/screenshot/capture")
async def capture(payload: ScreenshotRequest) -> dict:
    file_name = f"app-{payload.app_id}-{int(datetime.now(UTC).timestamp())}.png"
    target = SCREENSHOT_DIR / file_name

    image = Image.new("RGB", (1200, 720), color=(18, 24, 38))
    draw = ImageDraw.Draw(image)
    draw.text((48, 48), "Python AI Mother Screenshot Service", fill=(255, 255, 255))
    draw.text((48, 96), f"appId={payload.app_id}", fill=(200, 220, 255))
    draw.text((48, 144), payload.html_code[:300], fill=(170, 190, 220))
    image.save(target)
    return success(f"/static/screenshots/{file_name}")
