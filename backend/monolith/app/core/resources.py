from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from redis.asyncio import Redis

from app.core.config import Settings


class ResourceManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker | None = None
        self.redis_client: Redis | None = None

    async def start(self) -> None:
        if self.engine is None:
            self.engine = create_async_engine(
                self.settings.database_url,
                echo=self.settings.debug,
                pool_pre_ping=True,
            )
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
            )
        if self.redis_client is None:
            self.redis_client = Redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
            )

    async def stop(self) -> None:
        if self.redis_client is not None:
            await self.redis_client.aclose()
            self.redis_client = None
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

