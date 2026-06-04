"""Адаптер sherlock: поиск username по соцсетям → нормализованные social_account."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._proc import ToolError, run_cmd, temp_path

if TYPE_CHECKING:
    from . import NormalizedFinding


def run(kind: str, value: str) -> list["NormalizedFinding"]:
    from . import NormalizedFinding

    if kind != "username":
        raise ToolError("sherlock работает только с kind=username")

    out = temp_path(suffix=".json")
    # sherlock пишет JSON отчёт; --print-found ускоряет, но json даёт структуру
    proc = run_cmd(["sherlock", "--no-color", "--output", str(out), value])

    findings: list[NormalizedFinding] = []
    # sherlock (CLI) кладёт результаты в <value>.txt рядом; JSON-режим зависит от версии.
    # Парсим stdout как надёжный источник: строки "[+] Site: URL".
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("[+]") and "http" in line:
            try:
                site, url = line[3:].split(":", 1)
            except ValueError:
                continue
            url = url.strip()
            findings.append(
                NormalizedFinding(
                    entity_kind="social_account",
                    entity_value=url,
                    confidence=0.7,
                    raw={"site": site.strip(), "url": url, "username": value},
                )
            )

    out.unlink(missing_ok=True)
    return findings
