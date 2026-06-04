"""Тесты сервисной аутентификации (X-Aziral-Key) для автоматизации."""
from app import auth
from app.auth import get_current_user


def test_service_key_authenticates(monkeypatch):
    monkeypatch.setattr(auth.settings, "internal_api_key", "secret-key")
    monkeypatch.setattr(auth.settings, "dev_mode", False)
    user = get_current_user(None, None, None, x_aziral_key="secret-key")
    assert user.username == "service:automation"
    assert "service" in user.groups


def test_wrong_service_key_falls_through_to_dev(monkeypatch):
    monkeypatch.setattr(auth.settings, "internal_api_key", "secret-key")
    monkeypatch.setattr(auth.settings, "dev_mode", True)
    # неверный ключ → не сервис; dev_mode даёт dev-пользователя
    user = get_current_user(None, None, None, x_aziral_key="nope")
    assert user.username == "dev"


def test_sso_header_used_when_present(monkeypatch):
    monkeypatch.setattr(auth.settings, "dev_mode", False)
    user = get_current_user("alice", None, "admins|ops", x_aziral_key=None)
    assert user.username == "alice"
    assert "admins" in user.groups
