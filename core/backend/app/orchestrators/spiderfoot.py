"""Адаптер SpiderFoot: запуск скана через REST API, опрос и нормализация событий.

SpiderFoot работает как отдельный сервис (контейнер) со своим HTTP API.
Адаптер запускает скан, ждёт завершения (с таймаутом) и нормализует результаты
в единую схему findings. API SpiderFoot версионно-зависим, поэтому парсинг
максимально терпим к формату; при неожиданном ответе бросаем ToolError.
"""
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import httpx

from ._proc import ToolError

if TYPE_CHECKING:
    from . import NormalizedFinding

SPIDERFOOT_URL = os.getenv("SPIDERFOOT_URL", "http://spiderfoot:5001")
POLL_TIMEOUT = int(os.getenv("SPIDERFOOT_TIMEOUT", "600"))
POLL_INTERVAL = 10

# Тип события SpiderFoot → (kind в нашей схеме, индекс уверенности).
EVENT_MAP = {
    "EMAILADDR": "email",
    "EMAILADDR_GENERIC": "email",
    "DOMAIN_NAME": "domain",
    "INTERNET_NAME": "host",
    "INTERNET_NAME_UNRESOLVED": "host",
    "IP_ADDRESS": "ip",
    "IPV6_ADDRESS": "ip",
    "USERNAME": "username",
    "PHONE_NUMBER": "phone",
    "ACCOUNT_EXTERNAL_OWNED": "social_account",
    "HUMAN_NAME": "person",
    "PASSWORD_COMPROMISED": "breach",
    "EMAILADDR_COMPROMISED": "breach",
}


def _start_scan(client: httpx.Client, kind: str, value: str) -> str:
    """Стартует скан, возвращает его id."""
    payload = {
        "scanname": f"aziral-{kind}-{value}",
        "scantarget": value,
        "usecase": "all",
        "modulelist": "",
        "typelist": "",
    }
    resp = client.post("/startscan", data=payload, headers={"Accept": "application/json"})
    resp.raise_for_status()
    try:
        data = resp.json()
    except ValueError as exc:
        raise ToolError("SpiderFoot: неожиданный ответ /startscan (не JSON)") from exc
    # Ожидаемый формат: ["SUCCESS", "", "<scan_id>"]
    if isinstance(data, list) and len(data) >= 3 and data[0] == "SUCCESS":
        return str(data[2])
    raise ToolError(f"SpiderFoot не запустил скан: {data}")


def _wait_finished(client: httpx.Client, scan_id: str) -> None:
    deadline = time.monotonic() + POLL_TIMEOUT
    terminal = {"FINISHED", "ABORTED", "ERROR-FAILED", "FAILED"}
    while time.monotonic() < deadline:
        resp = client.get("/scanstatus", params={"id": scan_id})
        if resp.status_code == 200:
            try:
                status = resp.json()[0]
            except (ValueError, IndexError, KeyError):
                status = ""
            if status in terminal:
                return
        time.sleep(POLL_INTERVAL)
    raise ToolError(f"SpiderFoot: таймаут ожидания скана {scan_id}")


def _fetch_results(client: httpx.Client, scan_id: str) -> list["NormalizedFinding"]:
    from . import NormalizedFinding

    resp = client.get(
        "/scaneventresults",
        params={"id": scan_id, "eventType": "ALL", "filterfp": "True"},
    )
    resp.raise_for_status()
    try:
        rows = resp.json()
    except ValueError as exc:
        raise ToolError("SpiderFoot: /scaneventresults вернул не JSON") from exc

    findings: list[NormalizedFinding] = []
    for row in rows:
        # Типичная строка: [generated, data, source_data, module, event_type, ...]
        if not isinstance(row, list) or len(row) < 5:
            continue
        data_value, module, event_type = row[1], row[3], row[4]
        kind = EVENT_MAP.get(str(event_type))
        if not kind or not data_value:
            continue
        findings.append(
            NormalizedFinding(
                entity_kind=kind,
                entity_value=str(data_value),
                confidence=0.6,
                raw={"module": module, "event_type": event_type, "source": "spiderfoot"},
            )
        )
    return findings


def run(kind: str, value: str) -> list["NormalizedFinding"]:
    if kind not in ("domain", "host", "email", "ip", "username"):
        raise ToolError("SpiderFoot: неподдерживаемый kind")
    try:
        with httpx.Client(base_url=SPIDERFOOT_URL, timeout=30) as client:
            scan_id = _start_scan(client, kind, value)
            _wait_finished(client, scan_id)
            return _fetch_results(client, scan_id)
    except httpx.HTTPError as exc:
        raise ToolError(f"SpiderFoot недоступен: {exc}") from exc
