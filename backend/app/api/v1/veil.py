import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.models.veil_run import VeilRun
from app.schemas.veil_run import VeilRunOut, to_out
from app.services import veil_service

router = APIRouter(prefix="/veil", tags=["veil"])


@router.post("/enter", response_model=VeilRunOut)
def enter_veil(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> VeilRunOut:
    run = veil_service.enter_veil(db, current_user.hero)
    return to_out(run)


@router.get("/active", response_model=VeilRunOut | None)
def get_active_run(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> VeilRunOut | None:
    run = veil_service.get_active_run(db, current_user.hero)
    return to_out(run) if run is not None else None


@router.post("/{run_id}/claim", response_model=VeilRunOut)
def claim_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VeilRunOut:
    run = db.get(VeilRun, run_id)
    if run is None or run.hero_id != current_user.hero.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="veil run not found")

    claimed = veil_service.claim_run(db, run_id, current_user.hero.id)
    return to_out(claimed)
