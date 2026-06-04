"""Конфигурация Celery."""
from __future__ import annotations

from celery import Celery

from ..config import settings

celery_app = Celery(
    "aziral",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
