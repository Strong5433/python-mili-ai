from app.client.base import BaseServiceClient


class UserServiceClient(BaseServiceClient):
    async def validate_session(self, session_id: str | None) -> dict | None:
        if not session_id:
            return None
        return await self._get_json("/internal/session/validate", params={"sessionId": session_id})
