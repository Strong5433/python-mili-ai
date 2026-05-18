from app.client.base import BaseServiceClient


class ScreenshotServiceClient(BaseServiceClient):
    async def capture(self, app_id: int, html_code: str) -> str:
        data = await self._post_json(
            "/internal/screenshot/capture",
            payload={"appId": app_id, "htmlCode": html_code},
        )
        return str(data or "")
