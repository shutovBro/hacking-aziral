"""Celery-задачи: фактический запуск сканов и сохранение результатов."""
from __future__ import annotations

from ..db import SessionLocal
from ..models import Entity, Finding, Job, JobStatus
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

        saved = 0
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

        job.status = JobStatus.completed
        job.log = f"Готово. Сохранено findings: {saved}"
        db.commit()
        return {"job_id": job_id, "status": "completed", "findings": saved}
    finally:
        db.close()
