import asyncio
import time

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException


class RateLimitService:
    _memory_store: dict[str, tuple[int, float]] = {}
    _memory_lock = asyncio.Lock()

    def __init__(self, redis_client: Redis | None, settings: Settings) -> None:
        self.redis_client = redis_client
        self.settings = settings

    async def assert_chat_rate_limit(self, user_id: int, route: str) -> None:
        if user_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "Invalid user id")

        limit = max(1, int(self.settings.chat_rate_limit_count))
        window_seconds = max(1, int(self.settings.chat_rate_limit_window_seconds))
        key = f"ratelimit:chat:{route}:{user_id}"

        current = await self._incr(key, window_seconds)
        if current > limit:
            raise BusinessException(
                ErrorCode.PARAMS_ERROR,
                f"请求过于频繁，请在 {window_seconds} 秒后重试",
            )

    async def _incr(self, key: str, window_seconds: int) -> int:
        if self.redis_client is not None:
            incr_fn = getattr(self.redis_client, "incr", None)
            expire_fn = getattr(self.redis_client, "expire", None)
            try:
                if callable(incr_fn) and callable(expire_fn):
                    current = int(await incr_fn(key))
                    if current == 1:
                        await expire_fn(key, window_seconds)
                    return current
            except RedisError:
                pass

        now = time.monotonic()
        async with self._memory_lock:
            count, expire_at = self._memory_store.get(key, (0, 0.0))
            if now >= expire_at:
                count = 0
                expire_at = now + window_seconds
            count += 1
            self._memory_store[key] = (count, expire_at)
            return count
