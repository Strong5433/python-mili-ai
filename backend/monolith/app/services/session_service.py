import json
import logging
import secrets
import time
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SessionPayload:
    user_id: int
    user_role: str


class SessionService:
    _memory_store: dict[str, tuple[str, float]] = {}

    def __init__(self, redis_client: Redis | None, settings: Settings) -> None:
        self.redis_client = redis_client
        self.settings = settings

    def _session_key(self, session_id: str) -> str:
        return f"session:user:{session_id}"

    def _session_ttl(self) -> int:
        return max(int(self.settings.session_ttl_seconds), 60)

    @classmethod
    def _cleanup_memory_store(cls) -> None:
        now = time.time()
        expired_keys = [key for key, (_, expire_at) in cls._memory_store.items() if expire_at <= now]
        for key in expired_keys:
            cls._memory_store.pop(key, None)

    @classmethod
    def _memory_set(cls, session_key: str, payload_json: str, ttl_seconds: int) -> None:
        expire_at = time.time() + ttl_seconds
        cls._memory_store[session_key] = (payload_json, expire_at)

    @classmethod
    def _memory_get(cls, session_key: str) -> str | None:
        cls._cleanup_memory_store()
        value = cls._memory_store.get(session_key)
        if value is None:
            return None
        payload_json, expire_at = value
        if expire_at <= time.time():
            cls._memory_store.pop(session_key, None)
            return None
        return payload_json

    @classmethod
    def _memory_delete(cls, session_key: str) -> None:
        cls._memory_store.pop(session_key, None)

    async def create_session(self, user_id: int, user_role: str) -> str:
        session_id = secrets.token_urlsafe(32)
        session_key = self._session_key(session_id)
        ttl_seconds = self._session_ttl()
        payload_json = json.dumps({"userId": user_id, "userRole": user_role})
        await self._set_payload(session_key, payload_json, ttl_seconds)
        return session_id

    async def get_session(self, session_id: str) -> SessionPayload | None:
        session_key = self._session_key(session_id)
        payload_json = await self._get_payload(session_key)
        if not payload_json:
            return None
        try:
            parsed = json.loads(payload_json)
            user_id = int(parsed["userId"])
            user_role = str(parsed.get("userRole", "user"))
            return SessionPayload(user_id=user_id, user_role=user_role)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            await self.delete_session(session_id)
            return None

    async def delete_session(self, session_id: str) -> None:
        session_key = self._session_key(session_id)
        await self._delete_payload(session_key)

    async def _set_payload(self, session_key: str, payload_json: str, ttl_seconds: int) -> None:
        self._memory_set(session_key, payload_json, ttl_seconds)
        if self.redis_client is None:
            return
        try:
            await self.redis_client.setex(session_key, ttl_seconds, payload_json)
        except (RedisError, OSError) as exc:
            logger.warning("Redis setex failed, fallback to memory session store: %s", exc)

    async def _get_payload(self, session_key: str) -> str | None:
        if self.redis_client is not None:
            try:
                redis_value = await self.redis_client.get(session_key)
                if redis_value:
                    return redis_value
            except (RedisError, OSError) as exc:
                logger.warning("Redis get failed, fallback to memory session store: %s", exc)
        return self._memory_get(session_key)

    async def _delete_payload(self, session_key: str) -> None:
        self._memory_delete(session_key)
        if self.redis_client is None:
            return
        try:
            await self.redis_client.delete(session_key)
        except (RedisError, OSError) as exc:
            logger.warning("Redis delete failed, fallback to memory session store: %s", exc)
