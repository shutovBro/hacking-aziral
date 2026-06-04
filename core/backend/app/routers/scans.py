"""Запуск сканов с обязательной проверкой scope-gate."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..config import scope_settings
from ..db import get_db
from ..models import AuditLog, Job, JobStatus, Target
from ..orchestrators import available_tools
from ..scope import check_in_scope
from ..schemas import JobOut, ScanRequest

router = APIRouter(prefix="/scans", tags=["scans"])


def _audit(db: Session, actor: str, action: str, target_id: int | None, detail: dict, allowed: bool) -> None:
    db.add(AuditLog(actor=actor, action=action, target_id=target_id, detail=detail, allowed=allowed))


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def launch_scan(
    req: ScanRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Job:
    """Запускает разведку. Блокирует запуск вне scope (если SCOPE_MODE=enforce)."""
    target = db.get(Target, req.target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    if req.tool not in available_tools():
        raise HTTPException(status_code=400, detail=f"Инструмент недоступен. Доступны: {available_tools()}")

    decision = check_in_scope(target.scope, req.kind, req.value)
    detail = {"tool": req.tool, "kind": req.kind, "value": req.value, "reason": decision.reason}

    # SCOPE-GATE: вне scope → блок + аудит (в режиме enforce).
    if not decision.allowed and scope_settings.scope_mode == "enforce":
        job = Job(
            target_id=target.id,
            tool=req.tool,
            params={"kind": req.kind, "value": req.value},
            status=JobStatus.blocked,
            log=f"Заблокировано scope-gate: {decision.reason}",
            created_by=user.username,
        )
        db.add(job)
        _audit(db, user.username, "scan.blocked", target.id, detail, allowed=False)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Цель вне авторизованного scope: {decision.reason}",
        )

    # Разрешено (или warn-режим): создаём job и ставим в очередь.
    job = Job(
        target_id=target.id,
        tool=req.tool,
        params={"kind": req.kind, "value": req.value},
        status=JobStatus.pending,
        created_by=user.username,
        log="" if decision.allowed else f"WARN: {decision.reason} (scope_mode=warn)",
    )
    db.add(job)
    db.flush()
    _audit(db, user.username, "scan.launch", target.id, {**detail, "job_id": job.id}, allowed=True)
    db.commit()
    db.refresh(job)

    _enqueue(job.id)
    return job


def _enqueue(job_id: int) -> None:
    """Ставит задачу в Celery. Изолировано для простоты тестирования."""
    from ..workers.tasks import run_scan

    run_scan.delay(job_id)


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)) -> list[Job]:
    return db.query(Job).order_by(Job.created_at.desc()).limit(100).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return job
