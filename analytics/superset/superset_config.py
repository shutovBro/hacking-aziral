"""Конфигурация Apache Superset для Hacking-Aziral.

Метаданные Superset хранятся в отдельной БД (superset) того же Postgres-кластера.
БД с находками (aziral_core) подключается как источник данных (см. bootstrap.sh).
"""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# Метаданные самого Superset.
_user = os.environ.get("POSTGRES_USER", "aziral")
_pwd = os.environ.get("POSTGRES_PASSWORD", "")
_db = os.environ.get("SUPERSET_POSTGRES_DB", "superset")
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{_user}:{_pwd}@postgres:5432/{_db}"

# За обратным прокси (Traefik) — корректные схемы/заголовки.
ENABLE_PROXY_FIX = True

# Кеш на Redis (опционально, ускоряет дашборды).
_redis_pwd = os.environ.get("REDIS_PASSWORD", "")
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": f"redis://:{_redis_pwd}@redis:6379/2",
}

FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "EMBEDDED_SUPERSET": True,
}

# Подключение к источнику данных платформы (findings) — URI для bootstrap.
AZIRAL_FINDINGS_URI = f"postgresql+psycopg2://{_user}:{_pwd}@postgres:5432/aziral_core"
