"""Хелпер запуска внешних CLI-инструментов с таймаутом."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

DEFAULT_TIMEOUT = 300  # сек


class ToolError(RuntimeError):
    """Инструмент завершился с ошибкой или недоступен."""


def run_cmd(args: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
    """Запускает команду, возвращает CompletedProcess. Бросает ToolError при сбое запуска."""
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ToolError(f"Инструмент не установлен: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"Таймаут инструмента {args[0]} ({timeout}s)") from exc


def temp_path(suffix: str = "") -> Path:
    """Создаёт путь к временному файлу (без открытия)."""
    fd, name = tempfile.mkstemp(suffix=suffix)
    Path(name).unlink(missing_ok=True)
    return Path(name)
