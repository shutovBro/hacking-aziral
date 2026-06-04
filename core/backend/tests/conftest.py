"""Фикстуры pytest: изолированная БД и тестовый клиент."""
import os
import tempfile

import pytest

# До импорта приложения настраиваем окружение на временную SQLite-БД.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["CORE_DATABASE_URL"] = f"sqlite+pysqlite:///{_tmp.name}"
os.environ["SCOPE_MODE"] = "enforce"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import scans  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _no_celery(monkeypatch):
    # В тестах не ставим реальные задачи в Celery/Redis.
    monkeypatch.setattr(scans, "_enqueue", lambda job_id: None)


@pytest.fixture
def client():
    return TestClient(app)
