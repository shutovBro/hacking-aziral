"""Адаптер maigret: мегаинструмент поиска аккаунтов (3000+ сайтов).

Maigret ищет по никнейму/email везде. Интегрируем как subprocess с JSON-выводом.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._proc import ToolError, run_cmd, temp_path

if TYPE_CHECKING:
    from . import NormalizedFinding


def run(kind: str, value: str) -> list["NormalizedFinding"]:
    from . import NormalizedFinding

    if kind not in ("username", "email"):
        raise ToolError("maigret поддерживает только kind=username|email")

    out = temp_path(suffix=".json")
    # maigret может выдать JSON через --json флаг (если есть в версии) или CSV.
    # Более универсально: вызвать с --output json и парсить.
    try:
        proc = run_cmd(["maigret", "--json", value], timeout=600)
    except ToolError:
        # Фолбак: без флагов, текстовый вывод
        proc = run_cmd(["maigret", value], timeout=600)

    findings: list[NormalizedFinding] = []
    # Парс stdout: строки типа "Username: telegram, instagram, github"
    # или JSON результат (зависит от версии maigret).
    for line in proc.stdout.splitlines():
        if not line.strip() or line.startswith("[") or line.startswith("{"):
            continue  # прыгаем JSON/служебное
        tokens = line.split(":", 1)
        if len(tokens) == 2:
            site, _ = tokens
            site = site.strip()
            if site and "@" not in site:  # не email
                findings.append(
                    NormalizedFinding(
                        entity_kind="social_account",
                        entity_value=f"{site}:{value}",
                        confidence=0.75,
                        raw={"site": site, "query": value, "source": "maigret"},
                    )
                )
    out.unlink(missing_ok=True)
    return findings
