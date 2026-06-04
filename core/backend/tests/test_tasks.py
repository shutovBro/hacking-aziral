"""Тесты Celery-задачи run_scan (нормализация, дедупликация, статусы)."""
from app.db import SessionLocal
from app.models import Entity, Finding, Job, JobStatus, Target
from app.orchestrators import NormalizedFinding
from app.workers import tasks


def _seed_job(tool="sherlock", kind="username", value="alice") -> tuple[int, int]:
    db = SessionLocal()
    target = Target(name="t", scope={"usernames": ["alice"]})
    db.add(target)
    db.flush()
    job = Job(target_id=target.id, tool=tool, params={"kind": kind, "value": value},
              status=JobStatus.pending)
    db.add(job)
    db.commit()
    ids = (job.id, target.id)
    db.close()
    return ids


def test_run_scan_saves_and_dedupes(monkeypatch):
    twice = [
        NormalizedFinding("social_account", "https://x/alice", 0.7, {"n": 1}),
        NormalizedFinding("social_account", "https://x/alice", 0.7, {"n": 2}),
    ]
    monkeypatch.setattr(tasks, "run_tool", lambda tool, kind, value: twice)
    job_id, target_id = _seed_job()

    result = tasks.run_scan(job_id)
    assert result["status"] == "completed"
    assert result["findings"] == 2

    db = SessionLocal()
    assert db.query(Entity).filter_by(target_id=target_id).count() == 1  # дедуп сущности
    assert db.query(Finding).count() == 2
    assert db.get(Job, job_id).status == JobStatus.completed
    db.close()


def test_run_scan_handles_tool_error(monkeypatch):
    def boom(tool, kind, value):
        raise RuntimeError("инструмент упал")

    monkeypatch.setattr(tasks, "run_tool", boom)
    job_id, _ = _seed_job()

    result = tasks.run_scan(job_id)
    assert result["status"] == "failed"

    db = SessionLocal()
    assert db.get(Job, job_id).status == JobStatus.failed
    db.close()


def test_run_scan_missing_job():
    assert "error" in tasks.run_scan(999999)
