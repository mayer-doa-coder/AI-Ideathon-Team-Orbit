from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ConsultationRequest


class Expert(BaseModel):
    """A (mock) crop expert on the consultancy roster."""

    id: str
    name: str
    specialty: str
    credentials: str
    languages: list[str]
    avatar_initials: str


class ConsultationAccess(BaseModel):
    """Whether the current user has unlocked expert consultancy by paying.

    `has_premium` is the gate the frontend uses to show the consultancy desk
    vs. the upgrade prompt; the counts/last-payment fields let the UI explain
    *why* access is (not) granted without a second request."""

    has_premium: bool
    successful_payments: int
    last_payment_at: datetime | None = None


class ConsultationRequestCreate(BaseModel):
    expert_id: str = Field(..., description="id of a crop expert from GET /api/consultancy/experts")
    topic: str = Field(..., min_length=5, max_length=2000, description="The farmer's question for the expert")


class ConsultationRequestOut(BaseModel):
    id: int
    expert_id: str
    expert_name: str
    expert_specialty: str
    topic: str
    expert_reply: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_row(cls, row: ConsultationRequest) -> "ConsultationRequestOut":
        return cls.model_validate(row)
