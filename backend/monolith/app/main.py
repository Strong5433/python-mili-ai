from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.metrics import register_metrics
from app.core.middleware import register_middlewares
from app.core.resources import ResourceManager

settings = get_settings()
resources = ResourceManager(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await resources.start()
    app.state.resources = resources
    try:
        yield
    finally:
        await resources.stop()


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    generated_root = settings.generated_code_path()
    Path(generated_root).mkdir(parents=True, exist_ok=True)
    fastapi_app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    register_middlewares(fastapi_app, settings)
    register_metrics(fastapi_app)
    register_exception_handlers(fastapi_app)
    fastapi_app.include_router(api_router, prefix=settings.api_prefix)
    fastapi_app.mount(
        f"{settings.api_prefix}/static",
        StaticFiles(directory=str(generated_root), html=True),
        name="static",
    )
    return fastapi_app


app = create_app()
