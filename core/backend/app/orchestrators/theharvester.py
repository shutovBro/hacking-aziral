"""Адаптер theHarvester: сбор email/субдоменов/хостов по домену."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._proc import ToolError, run_cmd, temp_path

if TYPE_CHECKING:
    from . import NormalizedFinding

# Источники по умолчанию, не требующие API-ключей.
DEFAULT_SOURCES = "crtsh,duckduckgo,bing,certspotter,hackertarget,rapiddns"


def run(kind: str, value: str) -> list["NormalizedFinding"]:
    from . import NormalizedFinding

    if kind not in ("domain", "host"):
        raise ToolError("theHarvester работает с kind=domain|host")

    out = temp_path()  # theHarvester добавит .json сам при -f
    proc = run_cmd(
        ["theHarvester", "-d", value, "-b", DEFAULT_SOURCES, "-f", str(out)],
        timeout=420,
    )

    findings: list[NormalizedFinding] = []
    json_file = out.with_suffix(".json")
    if json_file.exists():
        try:
            data = json.loads(json_file.read_text())
        except json.JSONDecodeError:
            data = {}
        for email in data.get("emails", []) or []:
            findings.append(
                NormalizedFinding("email", email, 0.75, {"source": "theharvester", "domain": value})
            )
        for host in data.get("hosts", []) or []:
            findings.append(
                NormalizedFinding("host", host, 0.7, {"source": "theharvester", "domain": value})
            )
        for ip in data.get("ips", []) or []:
            findings.append(
                NormalizedFinding("ip", ip, 0.6, {"source": "theharvester", "domain": value})
            )
        json_file.unlink(missing_ok=True)

    if not findings:
        # Фолбэк: вытащим email/хосты из stdout, если JSON пуст.
        for line in proc.stdout.splitlines():
            tok = line.strip()
            if "@" in tok and "." in tok and " " not in tok:
                findings.append(
                    NormalizedFinding("email", tok, 0.6, {"source": "theharvester-stdout"})
                )

    out.unlink(missing_ok=True)
    return findings
