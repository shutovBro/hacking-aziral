"""Аутентификация через forward-auth заголовки Authentik.

Traefik+Authentik проверяют пользователя ДО Core и прокидывают заголовки
X-authentik-*. Здесь мы лишь читаем их. В dev-режиме (без заголовков) —
подставляется dev-пользователь, чтобы можно было работать локально без SSO.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from .config import settings


@dataclass(frozen=True)
class CurrentUser:
    username: str
    email: str
    groups: tuple[str, ...]


def get_current_user(
    x_authentik_username: str | None = Header(default=None),
    x_authentik_email: str | None = Header(default=None),
    x_authentik_groups: str | None = Header(default=None),
    x_aziral_key: str | None = Header(default=None),
) -> CurrentUser:
    """Возвращает текущего пользователя из SSO-заголовков или сервисного ключа."""
    # Сервис-аккаунт для автоматизации (только внутри internal-сети).
    if settings.internal_api_key and x_aziral_key == settings.internal_api_key:
        return CurrentUser("service:automation", "automation@local", ("service",))

    if x_authentik_username:
        groups = tuple(g.strip() for g in (x_authentik_groups or "").split("|") if g.strip())
        return CurrentUser(x_authentik_username, x_authentik_email or "", groups)

    if settings.dev_mode:
        return CurrentUser("dev", "dev@local", ("authentik Admins",))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Нет SSO-сессии (ожидались заголовки Authentik)",
    )


CurrentUserDep = Depends(get_current_user)
