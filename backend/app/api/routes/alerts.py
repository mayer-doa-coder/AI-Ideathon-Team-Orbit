from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Alert, Farm
from app.db.session import get_db
from app.models.user import User
from app.schemas.alert import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    farm_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Alert)
        .join(Farm, Alert.farm_id == Farm.id)
        .filter(Farm.user_id == current_user.id)
    )
    if farm_id is not None:
        query = query.filter(Alert.farm_id == farm_id)
    return query.order_by(Alert.created_at.desc()).all()


@router.post("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = (
        db.query(Alert)
        .join(Farm, Alert.farm_id == Farm.id)
        .filter(Alert.id == alert_id, Farm.user_id == current_user.id)
        .one_or_none()
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
