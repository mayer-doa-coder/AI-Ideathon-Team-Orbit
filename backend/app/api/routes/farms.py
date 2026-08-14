"""Minimal read-only farm lookup — enough for the monitor widgets to find
"my active farm". Creating/editing a farm profile is the conversation
agent's onboarding job (`ask_followup` / `persist`), not this route's."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Farm, Plan
from app.db.session import get_db
from app.models.user import User
from app.schemas.farm import FarmOut, PlanOut

router = APIRouter(prefix="/api/farms", tags=["farms"])


@router.get("/me", response_model=FarmOut)
def get_my_active_farm(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).one_or_none()
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active farm for this user yet"
        )
    return farm


@router.get("/me/plan", response_model=PlanOut)
def get_my_active_plan(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Reads `plans.season_plan`/`financials` straight from Postgres — the
    monitor graph's `write_alert` writes adjustments here directly, never
    through the conversation graph's checkpointer, so this is the only
    place a monitor-triggered change is visible after a page refresh."""
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).one_or_none()
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active farm for this user yet"
        )
    plan = db.query(Plan).filter(Plan.farm_id == farm.id).one_or_none()
    if plan is None:
        return PlanOut(crop=None, season_plan=None, financials=None)
    return PlanOut(crop=plan.selected_crop, season_plan=plan.season_plan, financials=plan.financials)
