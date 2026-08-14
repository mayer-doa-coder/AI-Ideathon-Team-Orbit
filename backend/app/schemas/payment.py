from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import BDAppsChargeTransaction

BDAPPS_SUCCESS_STATUS_CODE = "S1000"


class CheckoutRequest(BaseModel):
    msisdn: str = Field(..., description="Subscriber MSISDN to charge, e.g. 01605012802 or 8801605012802")
    amount: float = Field(..., gt=0, description="Amount in BDT to deduct from the subscriber's operator account")
    description: str = Field(default="AgriSense Premium Report", max_length=255)


class CheckoutReceipt(BaseModel):
    transaction_id: int
    external_trx_id: str
    internal_trx_id: str | None
    reference_id: str | None
    msisdn: str
    amount: float
    currency: str
    description: str | None
    status_code: str | None
    status_detail: str | None
    success: bool
    created_at: datetime

    @classmethod
    def from_transaction(cls, row: BDAppsChargeTransaction) -> "CheckoutReceipt":
        return cls(
            transaction_id=row.id,
            external_trx_id=row.external_trx_id,
            internal_trx_id=row.internal_trx_id,
            reference_id=row.reference_id,
            msisdn=row.msisdn,
            amount=row.amount,
            currency=row.currency,
            description=row.description,
            status_code=row.status_code,
            status_detail=row.status_detail,
            success=row.status_code == BDAPPS_SUCCESS_STATUS_CODE,
            created_at=row.created_at,
        )
