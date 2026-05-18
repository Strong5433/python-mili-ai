from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.code_gen_types import CODE_GEN_TYPE_VUE_PROJECT
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.core.config import Settings
from app.models.user import User
from app.services.app_service import AppService
from app.services.user_service import USER_ROLE_ADMIN

logger = logging.getLogger(__name__)


class ScreenshotService:
    async def capture_app_screenshot(
        self,
        db: AsyncSession,
        app_id: int,
        login_user: User,
        app_service: AppService,
        settings: Settings,
    ) -> str:
        app_entity = await app_service.get_app_entity_by_id(db, app_id)
        if app_entity.user_id != login_user.id and login_user.user_role != USER_ROLE_ADMIN:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "No permission")

        source_dir_name = f"{app_entity.code_gen_type}_{app_entity.id}"
        source_dir = settings.generated_code_path() / source_dir_name
        if not source_dir.exists() or not source_dir.is_dir():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "Generated code not found, please generate first")

        preview_entry = self._resolve_preview_entry(source_dir, app_entity.code_gen_type)
        screenshot_dir = source_dir / ".screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        file_name = f"screenshot_{timestamp}.png"
        screenshot_path = screenshot_dir / file_name

        deploy_key = app_entity.deploy_key or source_dir_name
        preview_url = f"{settings.deploy_domain.rstrip('/')}/{deploy_key}/{preview_entry.as_posix()}"
        self._render_placeholder_screenshot(screenshot_path, app_entity.app_name, preview_url)

        screenshot_url = (
            f"{settings.deploy_domain.rstrip('/')}/{source_dir_name}/.screenshots/{file_name}"
        )
        app_entity.cover = screenshot_url
        await db.commit()
        return screenshot_url

    @staticmethod
    def _resolve_preview_entry(source_dir: Path, code_gen_type: str) -> Path:
        if code_gen_type == CODE_GEN_TYPE_VUE_PROJECT and (source_dir / "dist" / "index.html").exists():
            return Path("dist/index.html")
        if (source_dir / "index.html").exists():
            return Path("index.html")

        html_files = sorted(path.relative_to(source_dir) for path in source_dir.rglob("*.html"))
        if html_files:
            return html_files[0]
        raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "No preview html found in generated files")

    @staticmethod
    def _render_placeholder_screenshot(target_path: Path, app_name: str, preview_url: str) -> None:
        width = 1280
        height = 720
        image = Image.new("RGB", (width, height), color=(249, 250, 251))
        draw = ImageDraw.Draw(image)

        draw.rectangle([(24, 24), (width - 24, height - 24)], outline=(203, 213, 225), width=3)
        draw.rectangle([(24, 24), (width - 24, 92)], fill=(15, 23, 42))

        draw.text((40, 46), "python-ai-mother screenshot", fill=(241, 245, 249))
        draw.text((40, 130), f"App: {app_name}", fill=(30, 41, 59))
        draw.text((40, 170), "Preview URL:", fill=(30, 41, 59))

        wrapped_lines = ScreenshotService._wrap_text(preview_url, max_chars=95)
        y = 208
        for line in wrapped_lines[:8]:
            draw.text((40, y), line, fill=(51, 65, 85))
            y += 32

        draw.text((40, height - 72), datetime.now(UTC).isoformat(), fill=(100, 116, 139))

        target_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(target_path, format="PNG")
        logger.info("Screenshot generated at %s", target_path)

    @staticmethod
    def _wrap_text(text: str, max_chars: int) -> list[str]:
        raw = (text or "").strip()
        if not raw:
            return [""]
        lines: list[str] = []
        idx = 0
        while idx < len(raw):
            lines.append(raw[idx : idx + max_chars])
            idx += max_chars
        return lines
