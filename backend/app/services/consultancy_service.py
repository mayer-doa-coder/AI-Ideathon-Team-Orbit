"""Expert-consultancy service — the paid feature unlocked by a real BDApps
payment.

The payment/entitlement side is real: `user_has_premium` reads the same
`BDAppsChargeTransaction` rows the CaaS checkout writes, and treats a user as
premium the moment they have one successful (`S1000`) charge. Everything about
the *experts* is deliberately mocked — a fixed roster and a templated reply —
so the demo shows the real payment gate driving a paid feature without standing
up an actual human advisory desk. Swapping `EXPERTS`/`compose_expert_reply` for
a real roster + messaging backend later leaves the payment gate untouched.
"""
from sqlalchemy.orm import Session

from app.db.models import BDAppsChargeTransaction, ConsultationRequest
from app.schemas.consultancy import ConsultationAccess, Expert

BDAPPS_SUCCESS_STATUS_CODE = "S1000"

# Fixed mock roster. `id` is what the frontend posts back on booking.
EXPERTS: list[Expert] = [
    Expert(
        id="rahman-rice",
        name="Dr. Anisur Rahman",
        specialty="Rice & cereal agronomy",
        credentials="PhD, BRRI — 15 yrs field advisory",
        languages=["Bangla", "English"],
        avatar_initials="AR",
    ),
    Expert(
        id="sultana-pest",
        name="Dr. Farzana Sultana",
        specialty="Plant pathology & pest management",
        credentials="PhD, BAU — disease diagnostics",
        languages=["Bangla", "English"],
        avatar_initials="FS",
    ),
    Expert(
        id="karim-soil",
        name="Md. Karim Uddin",
        specialty="Soil health & fertilizer planning",
        credentials="MSc Soil Science — 12 yrs extension",
        languages=["Bangla"],
        avatar_initials="KU",
    ),
    Expert(
        id="hasan-horti",
        name="Dr. Tanvir Hasan",
        specialty="Horticulture & vegetable crops",
        credentials="PhD Horticulture, SAU",
        languages=["Bangla", "English"],
        avatar_initials="TH",
    ),
]

EXPERTS_BY_ID: dict[str, Expert] = {expert.id: expert for expert in EXPERTS}


def get_experts() -> list[Expert]:
    return EXPERTS


def get_expert(expert_id: str) -> Expert | None:
    return EXPERTS_BY_ID.get(expert_id)


def _successful_charges(db: Session, user_id: int) -> list[BDAppsChargeTransaction]:
    return (
        db.query(BDAppsChargeTransaction)
        .filter(
            BDAppsChargeTransaction.user_id == user_id,
            BDAppsChargeTransaction.status_code == BDAPPS_SUCCESS_STATUS_CODE,
        )
        .order_by(BDAppsChargeTransaction.created_at.desc())
        .all()
    )


def user_has_premium(db: Session, user_id: int) -> bool:
    """True once the user has at least one successful BDApps charge."""
    return (
        db.query(BDAppsChargeTransaction.id)
        .filter(
            BDAppsChargeTransaction.user_id == user_id,
            BDAppsChargeTransaction.status_code == BDAPPS_SUCCESS_STATUS_CODE,
        )
        .first()
        is not None
    )


def get_access(db: Session, user_id: int) -> ConsultationAccess:
    charges = _successful_charges(db, user_id)
    return ConsultationAccess(
        has_premium=bool(charges),
        successful_payments=len(charges),
        last_payment_at=charges[0].created_at if charges else None,
    )


def compose_expert_reply(expert: Expert, topic: str) -> str:
    """Build the mock expert reply. Deterministic and templated on purpose —
    it references the farmer's question and the expert's specialty so it reads
    like a real first response, while staying an obvious stand-in for a human."""
    return (
        f"Assalamu alaikum, thank you for reaching out to Green Leaf expert desk.\n\n"
        f"Regarding your question — \"{topic.strip()}\" — here is my initial guidance "
        f"drawing on my work in {expert.specialty.lower()}:\n\n"
        f"1. Confirm the basics first: your crop's current growth stage, recent weather, "
        f"and any visible symptoms with photos help me narrow the cause quickly.\n"
        f"2. Act on the controllable factors now — balanced irrigation and correct "
        f"fertilizer timing prevent most of the issues farmers ask me about.\n"
        f"3. For a precise, farm-specific plan, share your district, soil type and the "
        f"variety you planted and I'll follow up with exact rates and a schedule.\n\n"
        f"I'll review your reply and get back to you shortly.\n"
        f"— {expert.name}, {expert.credentials}"
    )


def create_consultation(db: Session, user_id: int, expert: Expert, topic: str) -> ConsultationRequest:
    row = ConsultationRequest(
        user_id=user_id,
        expert_id=expert.id,
        expert_name=expert.name,
        expert_specialty=expert.specialty,
        topic=topic.strip(),
        expert_reply=compose_expert_reply(expert, topic),
        status="answered",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_consultations(db: Session, user_id: int) -> list[ConsultationRequest]:
    return (
        db.query(ConsultationRequest)
        .filter(ConsultationRequest.user_id == user_id)
        .order_by(ConsultationRequest.created_at.desc())
        .all()
    )
