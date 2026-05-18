from collections.abc import AsyncGenerator, Callable

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.codegen_routing_service import AiCodeGenTypeRoutingService
from app.core.config import Settings, get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessException
from app.core.ai_codegen_facade import AiCodeGeneratorFacade
from app.core.codegen_workflow import CodeGenWorkflowRunner
from app.models.user import User
from app.services.app_service import AppService
from app.services.chat_history_service import ChatHistoryService
from app.services.rate_limit_service import RateLimitService
from app.services.screenshot_service import ScreenshotService
from app.services.session_service import SessionService
from app.services.user_service import UserService


def get_app_settings() -> Settings:
    return get_settings()


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory = request.app.state.resources.session_factory
    if session_factory is None:
        raise BusinessException(ErrorCode.SYSTEM_ERROR, "Database is not ready")
    async with session_factory() as session:
        yield session


def get_redis_client(request: Request) -> Redis | None:
    return request.app.state.resources.redis_client


def get_user_service(
    settings: Settings = Depends(get_app_settings),
    redis_client: Redis | None = Depends(get_redis_client),
) -> UserService:
    return UserService(settings=settings, session_service=SessionService(redis_client, settings))


def get_app_service(
    settings: Settings = Depends(get_app_settings),
    redis_client: Redis | None = Depends(get_redis_client),
) -> AppService:
    return AppService(settings=settings, redis_client=redis_client)


def get_chat_history_service() -> ChatHistoryService:
    return ChatHistoryService()


def get_rate_limit_service(
    settings: Settings = Depends(get_app_settings),
    redis_client: Redis | None = Depends(get_redis_client),
) -> RateLimitService:
    return RateLimitService(redis_client=redis_client, settings=settings)


def get_ai_codegen_facade(settings: Settings = Depends(get_app_settings)) -> AiCodeGeneratorFacade:
    return AiCodeGeneratorFacade(settings=settings)


def get_codegen_workflow_runner(settings: Settings = Depends(get_app_settings)) -> CodeGenWorkflowRunner:
    return CodeGenWorkflowRunner(settings=settings)


def get_ai_routing_service(settings: Settings = Depends(get_app_settings)) -> AiCodeGenTypeRoutingService:
    return AiCodeGenTypeRoutingService(settings=settings)


def get_screenshot_service() -> ScreenshotService:
    return ScreenshotService()


async def get_login_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    user_service: UserService = Depends(get_user_service),
) -> User:
    session_id = request.cookies.get(settings.session_cookie_name)
    return await user_service.get_login_user_entity(db, session_id)


def require_role(required_role: str) -> Callable[..., User]:
    async def _verify_role(
        login_user: User = Depends(get_login_user),
        user_service: UserService = Depends(get_user_service),
    ) -> User:
        user_service.assert_role(login_user, required_role)
        return login_user

    return _verify_role
