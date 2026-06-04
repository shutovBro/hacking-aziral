"""Адаптер holehe: проверка, на каких сервисах зарегистрирован email."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._proc import ToolError, run_cmd, temp_path

if TYPE_CHECKING:
    from . import NormalizedFinding


def run(kind: str, value: str) -> list["NormalizedFinding"]:
    from . import NormalizedFinding

    if kind != "email":
        raise ToolError("holehe работает только с kind=email")

    out = temp_path(suffix=".json")
    # holehe умеет JSON-вывод через --only-used и -C (csv) / --json (зависит от версии)
    proc = run_cmd(["holehe", "--only-used", "--no-color", value])

    findings: list[NormalizedFinding] = []
    # Надёжный парс stdout: строки "[+] service.com" = аккаунт найден.
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("[+]"):
            service = line[3:].strip()
            if not service:
                continue
            findings.append(
                NormalizedFinding(
                    entity_kind="social_account",
                    entity_value=f"{service} ({value})",
                    confidence=0.8,
                    raw={"service": service, "email": value, "status": "used"},
                )
            )

    out.unlink(missing_ok=True)
    return findings
