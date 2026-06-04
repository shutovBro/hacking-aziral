"""Pydantic-схемы запросов/ответов API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScopeIn(BaseModel):
    domains: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    usernames: list[str] = Field(default_factory=list)
    hosts: list[str] = Field(default_factory=list)
    ip_ranges: list[str] = Field(default_factory=list)


class TargetCreate(BaseModel):
    name: str
    description: str = ""
    scope: ScopeIn = Field(default_factory=ScopeIn)
    authorized_by: str = ""


class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    scope: dict
    authorized_by: str
    created_by: str
    created_at: datetime


class ScanRequest(BaseModel):
    """Запрос на запуск разведки."""

    target_id: int
    tool: str = Field(description="sherlock | holehe | theharvester | spiderfoot | recon-ng")
    kind: str = Field(description="email | username | domain | host | ip")
    value: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_id: int
    tool: str
    status: str
    log: str
    created_at: datetime


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    value: str


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_tool: str
    confidence: float
    raw_json: dict
    discovered_at: datetime


class ApiError(BaseModel):
    detail: str
