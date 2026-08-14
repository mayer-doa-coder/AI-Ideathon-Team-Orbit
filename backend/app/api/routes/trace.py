from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Farm, TraceLog
from app.db.session import get_db
from app.models.user import User
from app.schemas.trace import TraceLogOut

router = APIRouter(prefix="/api/trace", tags=["trace"])


@router.get("/{farm_id}", response_model=list[TraceLogOut])
def get_trace_log(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = db.get(Farm, farm_id)
    if farm is None or farm.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    return (
        db.query(TraceLog)
        .filter(TraceLog.farm_id == farm_id)
        .order_by(TraceLog.created_at.desc())
        .limit(200)
        .all()
    )
