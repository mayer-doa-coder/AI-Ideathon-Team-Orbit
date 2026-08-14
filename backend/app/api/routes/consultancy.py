"""Expert-consultancy endpoints — the paid feature gated behind a real BDApps
CaaS payment.

Access is granted by `services.consultancy_service.user_has_premium`, which is
true once the user has a successful (`S1000`) charge from the checkout flow
(`api/routes/payment.checkout`). Booking a consultation returns a mocked expert
reply synchronously (see the service module) — the payment is real, the expert
desk is a stand-in.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.consultancy import (
    ConsultationAccess,
    ConsultationRequestCreate,
    ConsultationRequestOut,
    Expert,
)
from app.services import consultancy_service

router = APIRouter(prefix="/api/consultancy", tags=["consultancy"])


@router.get("/access", response_model=ConsultationAccess)
def get_access(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Whether this user has unlocked consultancy by paying, plus the counts
    the UI uses to explain access."""
    return consultancy_service.get_access(db, current_user.id)


@router.get("/experts", response_model=list[Expert])
def list_experts(current_user: User = Depends(get_current_user)):
    """The crop-expert roster. Not gated — the farmer can browse who they'd
    reach before paying; only booking requires premium."""
    return consultancy_service.get_experts()


@router.post("/requests", response_model=ConsultationRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: ConsultationRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not consultancy_service.user_has_premium(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Expert consultancy is a premium feature. Complete a payment to unlock it.",
        )

    expert = consultancy_service.get_expert(payload.expert_id)
    if expert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown expert")

    row = consultancy_service.create_consultation(db, current_user.id, expert, payload.topic)
    return ConsultationRequestOut.from_row(row)


@router.get("/requests", response_model=list[ConsultationRequestOut])
def list_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = consultancy_service.list_consultations(db, current_user.id)
    return [ConsultationRequestOut.from_row(row) for row in rows]
