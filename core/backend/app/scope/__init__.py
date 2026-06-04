"""Scope-gate: проверка, что цель скана входит в авторизованный scope."""
from .gate import ScopeDecision, check_in_scope

__all__ = ["ScopeDecision", "check_in_scope"]
