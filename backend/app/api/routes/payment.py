"""BDApps CaaS (Charging as a Service) checkout — the app-initiated side of
BDApps' direct-debit API (`tools/bdapps_client.direct_debit`), gated by the
same app configuration you set in the BDApps portal's CAAS tab ("Enable
Debit Requests", "Payment Instruments"). A checkout always writes a
`BDAppsChargeTransaction` row, whether BDApps accepts or rejects the charge —
that row *is* the receipt, so a failed charge is just as visible as a
successful one instead of silently disappearing.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import BDAppsChargeTransaction
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import CheckoutReceipt, CheckoutRequest
from app.tools import bdapps_client
from app.tools.bdapps_client import BDAppsAPIError, normalize_msisdn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.post("/checkout", response_model=CheckoutReceipt)
def checkout(payload: CheckoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msisdn = normalize_msisdn(payload.msisdn)
    external_trx_id = uuid.uuid4().hex

    try:
        result = bdapps_client.direct_debit(msisdn, external_trx_id, f"{payload.amount:.2f}")
    except BDAppsAPIError as exc:
        logger.warning("CaaS direct_debit failed for msisdn=%s: %s", msisdn, exc)
        row = BDAppsChargeTransaction(
            user_id=current_user.id,
            msisdn=msisdn,
            external_trx_id=external_trx_id,
            amount=payload.amount,
            currency="BDT",
            description=payload.description,
            status_code="E_LOCAL",
            status_detail=str(exc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    row = BDAppsChargeTransaction(
        user_id=current_user.id,
        msisdn=msisdn,
        external_trx_id=external_trx_id,
        internal_trx_id=result.get("internalTrxId"),
        reference_id=result.get("referenceId"),
        amount=payload.amount,
        currency="BDT",
        description=payload.description,
        status_code=result.get("statusCode"),
        status_detail=result.get("statusDetail"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CheckoutReceipt.from_transaction(row)


@router.get("/receipt/{external_trx_id}", response_model=CheckoutReceipt)
def get_receipt(external_trx_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(BDAppsChargeTransaction).filter(
        BDAppsChargeTransaction.external_trx_id == external_trx_id
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No transaction with that ID")
    return CheckoutReceipt.from_transaction(row)


@router.get("/history", response_model=list[CheckoutReceipt])
def list_history(msisdn: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(BDAppsChargeTransaction)
        .filter(BDAppsChargeTransaction.msisdn == normalize_msisdn(msisdn))
        .order_by(BDAppsChargeTransaction.created_at.desc())
        .all()
    )
    return [CheckoutReceipt.from_transaction(row) for row in rows]
