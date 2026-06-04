"""Точка входа FastAPI для Aziral Core."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import init_db
from .routers import findings, health, scans, targets


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MVP: создаём таблицы при старте. На проде заменить на Alembic.
    init_db()
    yield


app = FastAPI(
    title="Hacking-Aziral Core",
    description="Control plane авторизованной OSINT-платформы",
    version="0.1.0",
    lifespan=lifespan,
)

# Все маршруты под /api (Traefik роутит Host+/api на backend).
app.include_router(health.router, prefix="/api")
app.include_router(targets.router, prefix="/api")
app.include_router(findings.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
