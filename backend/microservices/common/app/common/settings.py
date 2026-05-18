from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    app_name: str = "python-ai-mother-microservice"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    session_cookie_name: str = "python_ai_mother_sid"
    user_service_base_url: str = "http://localhost:8201"
    ai_service_base_url: str = "http://localhost:8202"
    screenshot_service_base_url: str = "http://localhost:8204"
    generated_code_dir: str = "./generated"
    screenshot_dir: str = "./screenshots"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_service_settings() -> ServiceSettings:
    return ServiceSettings()
