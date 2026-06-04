"""Оркестрация OSINT-инструментов: единый интерфейс запуска и нормализации.

Каждый адаптер принимает (kind, value) и возвращает список NormalizedFinding.
Реестр TOOL_REGISTRY связывает имя инструмента с его адаптером.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import holehe as _holehe
from . import maigret as _maigret
from . import sherlock as _sherlock
from . import spiderfoot as _spiderfoot
from . import theharvester as _theharvester


@dataclass
class NormalizedFinding:
    """Нормализованный результат для записи в БД (entities + findings)."""

    entity_kind: str
    entity_value: str
    confidence: float = 0.5
    raw: dict = field(default_factory=dict)


# Реестр инструментов: имя → callable(kind, value) -> list[NormalizedFinding]
TOOL_REGISTRY = {
    "sherlock": _sherlock.run,
    "holehe": _holehe.run,
    "theharvester": _theharvester.run,
    "spiderfoot": _spiderfoot.run,
    "maigret": _maigret.run,
}


def available_tools() -> list[str]:
    return sorted(TOOL_REGISTRY)


def run_tool(tool: str, kind: str, value: str) -> list[NormalizedFinding]:
    """Запускает инструмент по имени. Бросает KeyError, если инструмент неизвестен."""
    adapter = TOOL_REGISTRY.get(tool)
    if adapter is None:
        raise ValueError(f"Неизвестный инструмент: {tool}. Доступны: {available_tools()}")
    return adapter(kind, value)
