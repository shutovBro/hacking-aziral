"""Алерты на критичные findings.

Стратегия:
- Если задан ``CORE_ALERT_WEBHOOK_URL`` — шлём POST туда (Activepieces flow,
  generic webhook и т.п.).
- Иначе, если заданы ``CORE_TELEGRAM_BOT_TOKEN`` + ``CORE_TELEGRAM_CHAT_ID`` —
  шлём напрямую в Telegram.
- Иначе — silently noop (логируем, чтобы было видно).

Порог: confidence >= ``CORE_ALERT_MIN_CONFIDENCE`` (по умолчанию 0.8).

Все ошибки доставки логируются и не валят основной поток скана.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass
from typing import Final
from urllib.error import URLError

logger = logging.getLogger(__name__)

_REQ_TIMEOUT_SECONDS: Final[float] = 5.0
_DEFAULT_MIN_CONFIDENCE: Final[float] = 0.8


@dataclass(frozen=True)
class AlertContext:
    """Минимальный контекст для алерта."""

    target_name: str
    tool: str
    entity_kind: str
    entity_value: str
    confidence: float


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid %s=%r, falling back to %s", name, raw, default)
        return default


def _post_json(url: str, payload: dict, headers: dict | None = None) -> None:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_REQ_TIMEOUT_SECONDS) as resp:
        if resp.status >= 300:
            logger.warning("alert webhook %s -> HTTP %s", url, resp.status)


def _send_webhook(url: str, ctx: AlertContext) -> None:
    payload = {
        "target": ctx.target_name,
        "tool": ctx.tool,
        "entity_kind": ctx.entity_kind,
        "entity_value": ctx.entity_value,
        "confidence": ctx.confidence,
    }
    _post_json(url, payload)


def _send_telegram(token: str, chat_id: str, ctx: AlertContext) -> None:
    text = (
        f"🚨 *Высокий риск finding* \\(`{ctx.confidence:.2f}`\\)\n\n"
        f"📋 Target: `{ctx.target_name}`\n"
        f"🛠 Tool: `{ctx.tool}`\n"
        f"🔖 {ctx.entity_kind}: `{ctx.entity_value}`"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    _post_json(url, {"chat_id": chat_id, "parse_mode": "MarkdownV2", "text": text})


def maybe_alert(ctx: AlertContext) -> None:
    """Отправляет алерт если confidence выше порога. Никогда не бросает наружу."""
    threshold = _env_float("CORE_ALERT_MIN_CONFIDENCE", _DEFAULT_MIN_CONFIDENCE)
    if ctx.confidence < threshold:
        return

    webhook_url = os.getenv("CORE_ALERT_WEBHOOK_URL", "").strip()
    tg_token = os.getenv("CORE_TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("CORE_TELEGRAM_CHAT_ID", "").strip()

    try:
        if webhook_url:
            _send_webhook(webhook_url, ctx)
        elif tg_token and tg_chat:
            _send_telegram(tg_token, tg_chat, ctx)
        else:
            logger.debug("alert skipped: no webhook or telegram configured")
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning("alert delivery failed: %s", exc)
