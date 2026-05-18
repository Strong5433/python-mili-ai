from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "python-ai-mother-backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: str = "*"
    database_url: str = "sqlite+aiosqlite:///./python_ai_mother.db"
    redis_url: str = "redis://localhost:6379/0"
    password_salt: str = "python-ai-mother"
    session_cookie_name: str = "python_ai_mother_sid"
    session_ttl_seconds: int = 86400
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model_name: str = "gpt-4o-mini"
    llm_stream: bool = True
    llm_timeout_seconds: float = 180.0
    llm_retry_count: int = 1
    ai_concurrency_limit: int = 4
    llm_max_prompt_chars: int = 12000
    prompt_block_keywords: str = "rm -rf,删库,提权,System prompt"
    generated_code_dir: str = "./generated"
    deploy_domain: str = "http://localhost:8123/api/static"
    app_query_cache_ttl_seconds: int = 30
    chat_rate_limit_count: int = 20
    chat_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        if normalized in {"release", "prod", "production", "false", "0", "off", "no"}:
            return False
        if normalized in {"debug", "dev", "development", "true", "1", "on", "yes"}:
            return True
        return value

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def normalize_llm_base_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return value.strip().rstrip("/")

    def generated_code_path(self) -> Path:
        return Path(self.generated_code_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
