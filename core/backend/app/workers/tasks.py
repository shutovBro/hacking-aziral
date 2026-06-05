"""Celery-задачи: фактический запуск сканов и сохранение результатов."""
from __future__ import annotations

from ..alerts import AlertContext, maybe_alert
from ..db import SessionLocal
from ..models import Entity, Finding, Job, JobStatus, Target
from ..orchestrators import run_tool
from .celery_app import celery_app


def _upsert_entity(db, target_id: int, kind: str, value: str) -> Entity:
    """Находит или создаёт сущность (дедупликация по target+kind+value)."""
    existing = (
        db.query(Entity)
        .filter(Entity.target_id == target_id, Entity.kind == kind, Entity.value == value)
        .one_or_none()
    )
    if existing:
        return existing
    entity = Entity(target_id=target_id, kind=kind, value=value)
    db.add(entity)
    db.flush()
    return entity


@celery_app.task(name="aziral.run_scan")
def run_scan(job_id: int) -> dict:
    """Выполняет скан job_id: запускает инструмент, нормализует, пишет findings."""
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return {"error": f"job {job_id} not found"}

        job.status = JobStatus.running
        db.commit()

        try:
            results = run_tool(job.tool, job.params.get("kind", ""), job.params.get("value", ""))
        except Exception as exc:  # noqa: BLE001 — фиксируем причину в логе задачи
            job.status = JobStatus.failed
            job.log = f"Ошибка инструмента {job.tool}: {exc}"
            db.commit()
            return {"job_id": job_id, "status": "failed", "error": str(job.log)}

        target = db.get(Target, job.target_id)
        target_name = target.name if target else f"#{job.target_id}"

        saved = 0
        alert_buffer: list[AlertContext] = []
        for item in results:
            entity = _upsert_entity(db, job.target_id, item.entity_kind, item.entity_value)
            db.add(
                Finding(
                    entity_id=entity.id,
                    source_tool=job.tool,
                    raw_json=item.raw,
                    confidence=item.confidence,
                )
            )
            saved += 1
            alert_buffer.append(
                AlertContext(
                    target_name=target_name,
                    tool=job.tool,
                    entity_kind=item.entity_kind,
                    entity_value=item.entity_value,
                    confidence=item.confidence,
                )
            )

        job.status = JobStatus.completed
        job.log = f"Готово. Сохранено findings: {saved}"
        db.commit()

        # Алерты — после commit'а, чтобы не блокировать запись при сбоях доставки.
        for ctx in alert_buffer:
            maybe_alert(ctx)
        return {"job_id": job_id, "status": "completed", "findings": saved}
    finally:
        db.close()
