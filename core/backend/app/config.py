"""Настройки приложения из окружения."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация Aziral Core. Все значения берутся из ENV."""

    model_config = SettingsConfigDict(env_prefix="CORE_", extra="ignore")

    secret_key: str = "dev-insecure-change-me"
    # По умолчанию SQLite для локального запуска тестов без Postgres.
    database_url: str = "sqlite+pysqlite:///./aziral_core.db"
    redis_url: str = "redis://localhost:6379/0"

    # Заголовки от Authentik forward-auth.
    auth_header_user: str = "x-authentik-username"
    auth_header_email: str = "x-authentik-email"
    auth_header_groups: str = "x-authentik-groups"

    # Режим dev: если True, при отсутствии заголовков SSO используется dev-пользователь.
    dev_mode: bool = True

    # Сервисный ключ для вызовов от автоматизации (activepieces/cronicle) по внутренней сети.
    # Если задан, запрос с заголовком X-Aziral-Key == значению аутентифицируется как сервис.
    internal_api_key: str = ""


# SCOPE_MODE читается отдельно (без префикса CORE_), т.к. общий для всей платформы.
class ScopeSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    scope_mode: str = "enforce"  # enforce | warn


settings = Settings()
scope_settings = ScopeSettings()
