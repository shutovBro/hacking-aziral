"""CRUD авторизованных целей."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import AuditLog, Target
from ..schemas import TargetCreate, TargetOut

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=list[TargetOut])
def list_targets(db: Session = Depends(get_db)) -> list[Target]:
    return db.query(Target).order_by(Target.created_at.desc()).all()


@router.post("", response_model=TargetOut, status_code=status.HTTP_201_CREATED)
def create_target(
    payload: TargetCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Target:
    target = Target(
        name=payload.name,
        description=payload.description,
        scope=payload.scope.model_dump(),
        authorized_by=payload.authorized_by,
        created_by=user.username,
    )
    db.add(target)
    db.flush()
    db.add(
        AuditLog(
            actor=user.username,
            action="target.create",
            target_id=target.id,
            detail={"name": target.name, "scope": target.scope},
            allowed=True,
        )
    )
    db.commit()
    db.refresh(target)
    return target


@router.get("/{target_id}", response_model=TargetOut)
def get_target(target_id: int, db: Session = Depends(get_db)) -> Target:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return target
