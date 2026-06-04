"""Health-check и метаданные платформы."""
from __future__ import annotations

from fastapi import APIRouter

from ..orchestrators import available_tools

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "aziral-core"}


@router.get("/tools")
def tools() -> dict:
    """Список доступных OSINT-инструментов."""
    return {"tools": available_tools()}
