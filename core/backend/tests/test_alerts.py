"""Тесты алертов: порог confidence, выбор канала (webhook/telegram), отказоустойчивость."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.alerts import AlertContext, maybe_alert


def _ctx(confidence: float = 0.9) -> AlertContext:
    return AlertContext(
        target_name="t1",
        tool="sherlock",
        entity_kind="social_account",
        entity_value="github.com/x",
        confidence=confidence,
    )


@pytest.mark.unit
def test_skip_when_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORE_ALERT_MIN_CONFIDENCE", "0.8")
    monkeypatch.setenv("CORE_ALERT_WEBHOOK_URL", "http://hook.local/x")
    with patch("app.alerts._send_webhook") as send:
        maybe_alert(_ctx(confidence=0.7))
        send.assert_not_called()


@pytest.mark.unit
def test_webhook_preferred_over_telegram(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORE_ALERT_WEBHOOK_URL", "http://hook.local/x")
    monkeypatch.setenv("CORE_TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("CORE_TELEGRAM_CHAT_ID", "1")
    with (
        patch("app.alerts._send_webhook") as send_hook,
        patch("app.alerts._send_telegram") as send_tg,
    ):
        maybe_alert(_ctx())
        send_hook.assert_called_once()
        send_tg.assert_not_called()


@pytest.mark.unit
def test_telegram_when_no_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORE_ALERT_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("CORE_TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("CORE_TELEGRAM_CHAT_ID", "1")
    with patch("app.alerts._send_telegram") as send_tg:
        maybe_alert(_ctx())
        send_tg.assert_called_once_with("tok", "1", _ctx())


@pytest.mark.unit
def test_noop_when_nothing_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("CORE_ALERT_WEBHOOK_URL", "CORE_TELEGRAM_BOT_TOKEN", "CORE_TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(var, raising=False)
    with (
        patch("app.alerts._send_webhook") as send_hook,
        patch("app.alerts._send_telegram") as send_tg,
    ):
        maybe_alert(_ctx())
        send_hook.assert_not_called()
        send_tg.assert_not_called()


@pytest.mark.unit
def test_delivery_failure_is_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORE_ALERT_WEBHOOK_URL", "http://broken/x")
    with patch("app.alerts._send_webhook", side_effect=OSError("connection refused")):
        # Не должна бросить — иначе разломает worker pipeline.
        maybe_alert(_ctx())
