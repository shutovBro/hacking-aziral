"""Просмотр нормализованных сущностей и находок по цели (Results Explorer)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Entity, Finding, Target
from ..schemas import EntityOut, FindingOut

router = APIRouter(prefix="/targets/{target_id}", tags=["results"])


@router.get("/entities", response_model=list[EntityOut])
def list_entities(target_id: int, db: Session = Depends(get_db)) -> list[Entity]:
    if db.get(Target, target_id) is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return db.query(Entity).filter(Entity.target_id == target_id).order_by(Entity.kind).all()


@router.get("/findings", response_model=list[FindingOut])
def list_findings(target_id: int, db: Session = Depends(get_db)) -> list[Finding]:
    if db.get(Target, target_id) is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return (
        db.query(Finding)
        .join(Entity, Finding.entity_id == Entity.id)
        .filter(Entity.target_id == target_id)
        .order_by(Finding.discovered_at.desc())
        .all()
    )
