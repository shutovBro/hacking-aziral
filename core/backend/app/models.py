"""ORM-модели единой схемы данных: targets → entities → findings (+ jobs, audit_log)."""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EntityKind(str, enum.Enum):
    email = "email"
    username = "username"
    domain = "domain"
    host = "host"
    person = "person"
    social_account = "social_account"
    breach = "breach"
    phone = "phone"
    ip = "ip"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"  # отклонён scope-gate


class Target(Base):
    """Авторизованная цель разведки + её scope."""

    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    # scope: {"domains":[],"emails":[],"usernames":[],"hosts":[],"ip_ranges":[]}
    scope: Mapped[dict] = mapped_column(JSON, default=dict)
    authorized_by: Mapped[str] = mapped_column(String(255), default="")
    created_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    entities: Mapped[list["Entity"]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )


class Entity(Base):
    """Нормализованная сущность, обнаруженная при разведке."""

    __tablename__ = "entities"
    __table_args__ = (Index("ix_entity_target_kind_value", "target_id", "kind", "value", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    kind: Mapped[EntityKind] = mapped_column(Enum(EntityKind))
    value: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    target: Mapped[Target] = relationship(back_populates="entities")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )


class Finding(Base):
    """Конкретное наблюдение по сущности из конкретного инструмента."""

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"))
    source_tool: Mapped[str] = mapped_column(String(64))
    raw_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    entity: Mapped[Entity] = relationship(back_populates="findings")


class Job(Base):
    """Запуск скана: статус, параметры, результат scope-проверки."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"))
    tool: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    celery_id: Mapped[str] = mapped_column(String(64), default="")
    log: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AuditLog(Base):
    """Кто/что/когда запускал и результат scope-gate."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id"), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
