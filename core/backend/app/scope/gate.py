"""Чистая логика scope-gate.

Решает, входит ли значение (email/username/domain/host/ip) в авторизованный scope цели.
Функция не зависит от БД и FastAPI — её легко покрыть unit-тестами.
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import NamedTuple


class ScopeDecision(NamedTuple):
    allowed: bool
    reason: str


@dataclass(frozen=True)
class Scope:
    """Нормализованное представление scope цели."""

    domains: tuple[str, ...] = ()
    emails: tuple[str, ...] = ()
    usernames: tuple[str, ...] = ()
    hosts: tuple[str, ...] = ()
    ip_ranges: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict | None) -> "Scope":
        data = data or {}
        norm = lambda items: tuple(str(i).strip().lower() for i in (items or []) if str(i).strip())
        return cls(
            domains=norm(data.get("domains")),
            emails=norm(data.get("emails")),
            usernames=norm(data.get("usernames")),
            hosts=norm(data.get("hosts")),
            ip_ranges=norm(data.get("ip_ranges")),
        )

    def is_empty(self) -> bool:
        return not (self.domains or self.emails or self.usernames or self.hosts or self.ip_ranges)


def _domain_matches(value: str, domains: tuple[str, ...]) -> bool:
    """value совпадает с доменом или является его поддоменом."""
    return any(value == d or value.endswith("." + d) for d in domains)


def _check_email(value: str, scope: Scope) -> ScopeDecision:
    if value in scope.emails:
        return ScopeDecision(True, "email явно в scope")
    domain = value.rsplit("@", 1)[-1] if "@" in value else ""
    if domain and _domain_matches(domain, scope.domains):
        return ScopeDecision(True, f"домен email {domain} в scope")
    return ScopeDecision(False, "email вне scope")


def _check_username(value: str, scope: Scope) -> ScopeDecision:
    if value in scope.usernames:
        return ScopeDecision(True, "username в scope")
    return ScopeDecision(False, "username вне scope")


def _check_domain_or_host(value: str, scope: Scope) -> ScopeDecision:
    if value in scope.hosts:
        return ScopeDecision(True, "host явно в scope")
    if _domain_matches(value, scope.domains):
        return ScopeDecision(True, "домен/поддомен в scope")
    return ScopeDecision(False, "домен/host вне scope")


def _check_ip(value: str, scope: Scope) -> ScopeDecision:
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return ScopeDecision(False, "невалидный IP")
    for cidr in scope.ip_ranges:
        try:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return ScopeDecision(True, f"IP в диапазоне {cidr}")
        except ValueError:
            continue
    return ScopeDecision(False, "IP вне scope")


_CHECKERS = {
    "email": _check_email,
    "username": _check_username,
    "domain": _check_domain_or_host,
    "host": _check_domain_or_host,
    "ip": _check_ip,
}


def check_in_scope(scope_data: dict | None, kind: str, value: str) -> ScopeDecision:
    """Главная проверка scope-gate.

    Пустой scope трактуется как «ничего не разрешено» (fail-closed).
    """
    scope = Scope.from_dict(scope_data)
    value = (value or "").strip().lower()
    if not value:
        return ScopeDecision(False, "пустое значение")
    if scope.is_empty():
        return ScopeDecision(False, "scope пуст — запрещено по умолчанию (fail-closed)")
    checker = _CHECKERS.get(kind)
    if checker is None:
        return ScopeDecision(False, f"неизвестный тип цели: {kind}")
    return checker(value, scope)
