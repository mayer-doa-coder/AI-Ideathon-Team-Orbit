"""BDApps callback endpoints.

These are the public callback URLs registered in the BDApps application
configuration (USSD, SMS, CaaS charging, subscription notifications),
implemented against the BDApps TAP API documentation
(https://dev.bdapps.com/API_Documentation/bdapps_tap_api.html).

- `/ussd` and `/sms` route the subscriber's text through the same
  conversation agent (`app.agents.graph_conversation.conversation_graph`)
  the web chat UI uses, keyed by the subscriber's MSISDN. Not gated on
  subscription status — this app's BDApps config has "Subscription
  Required" set to NO for both channels, so any inbound message gets
  answered regardless of `db.models.BDAppsSubscriber`.
- `/subscription-notification` is the one inbound callback that carries
  `applicationId`/`password`, so it's the one place we can authenticate that
  a callback genuinely came from BDApps; it keeps `BDAppsSubscriber` in sync.
- `/charging-notification` has no documented payload schema in the TAP API
  (CaaS charging via `caas/direct/debit` is synchronous — its own response
  is the result), so it stays a lightweight placeholder — only its ack shape
  is fixed to match BDApps's contract.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agents.graph_conversation import conversation_graph
from app.core.config import settings
from app.db.models import BDAppsSubscriber
from app.db.session import get_db
from app.schemas.bdapps import (
    BDAppsAckResponse,
    SmsReceiveRequest,
    SmsReportRequest,
    SubscriptionNotifyRequest,
    UssdReceiveRequest,
)
from app.tools import bdapps_client
from app.tools.bdapps_client import BDAppsAPIError, normalize_msisdn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bdapps", tags=["bdapps"])

# BDApps doesn't document an exact USSD character cap; this is a conservative
# single-screen budget so a long AI answer doesn't get silently truncated by
# the carrier's own USSD gateway instead.
USSD_MAX_CHARS = 300
USSD_PROMPT = "Welcome to AgriSense! Type your farming question:"


async def _peek(request: Request) -> None:
    """Log that a callback was received without dumping the payload.

    We only record the content type and payload size — never the body itself —
    so no subscriber MSISDNs, tokens, or other sensitive fields end up in logs.
    """
    body = await request.body()
    logger.info(
        "BDApps callback received: path=%s content_type=%s bytes=%d",
        request.url.path,
        request.headers.get("content-type", "unknown"),
        len(body),
    )


def _strip_sms_keyword(message: str) -> str:
    """BDApps routes an inbound SMS to this app only when it starts with the
    app's provisioned keyword (`SMS Keyword` in the portal's SMS tab) — strip
    it so the agent sees the farmer's actual question, not the routing
    prefix. Tolerates BDApps having already stripped it itself (unclear from
    the TAP API docs which side does it), so this is a no-op either way."""
    keyword = settings.bdapps_sms_keyword.strip()
    if not keyword:
        return message.strip()
    stripped = message.strip()
    if stripped.lower().startswith(keyword.lower()):
        stripped = stripped[len(keyword):].strip()
    return stripped


def _invoke_agent(msisdn: str, message: str) -> str:
    """Run one turn of the conversation agent for this MSISDN and return the
    latest AI reply text. Reuses `conversation_graph` exactly as `chat.py`
    does for the web UI, keyed on the MSISDN instead of a web user id.

    Any node failure is caught here rather than left to propagate: an
    unhandled exception would turn into a 500 on the callback itself, which
    BDApps would read as "delivery failed" and likely retry — we'd rather
    ack the inbound message and tell the farmer something went wrong."""
    config = {"configurable": {"thread_id": msisdn}}
    input_state = {
        "messages": [HumanMessage(content=message)],
        "farmer_id": msisdn,
        "turn_complete": False,
        "is_scenario": False,
        "current_location": None,
        "uploaded_image": None,
    }
    try:
        result_state = conversation_graph.invoke(input_state, config)
    except Exception:
        logger.exception("Conversation agent invocation failed for an SMS/USSD message")
        return "Sorry, something went wrong on our end. Please try again shortly."

    for msg in reversed(result_state["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return "Sorry, I couldn't process that. Please try again."


@router.post(
    "/ussd",
    status_code=status.HTTP_200_OK,
    response_model=BDAppsAckResponse,
    summary="BDApps USSD Connection URL",
    description=(
        "Receives USSD requests from BDApps (`ussd/receive`). Configure this "
        "URL as the USSD **Connection URL** in the BDApps application "
        "configuration. USSD is single-turn: `mo-init` gets a prompt "
        "(pushed back via `ussd/send` with `mt-cont`); the follow-up "
        "`mo-cont` question is answered by the conversation agent and the "
        "session ends (`mt-fin`)."
    ),
)
def ussd_callback(payload: UssdReceiveRequest):
    msisdn = normalize_msisdn(payload.sourceAddress)

    if payload.ussdOperation == "mo-init":
        try:
            bdapps_client.send_ussd(payload.sessionId, msisdn, USSD_PROMPT, "mt-cont")
        except BDAppsAPIError:
            logger.exception("Failed to send USSD prompt")
        return BDAppsAckResponse()

    reply = _invoke_agent(msisdn, payload.message)
    if len(reply) > USSD_MAX_CHARS:
        reply = reply[: USSD_MAX_CHARS - 3] + "..."
    try:
        bdapps_client.send_ussd(payload.sessionId, msisdn, reply, "mt-fin")
    except BDAppsAPIError:
        logger.exception("Failed to send USSD reply")
    return BDAppsAckResponse()


@router.post(
    "/sms",
    status_code=status.HTTP_200_OK,
    response_model=BDAppsAckResponse,
    summary="BDApps SMS Message Receiving URL",
    description=(
        "Receives incoming SMS (MO) messages from BDApps (`sms/receive`). "
        "Configure this URL as the SMS **Message Receiving URL** in the "
        "BDApps application configuration. The reply is generated by the "
        "conversation agent and sent back separately via `sms/send`."
    ),
)
def sms_callback(payload: SmsReceiveRequest):
    msisdn = normalize_msisdn(payload.sourceAddress)
    question = _strip_sms_keyword(payload.message)

    reply = _invoke_agent(msisdn, question)
    try:
        bdapps_client.send_sms(msisdn, reply)
    except BDAppsAPIError:
        logger.exception("Failed to send SMS reply")
    return BDAppsAckResponse()


@router.post(
    "/sms-delivery-report",
    status_code=status.HTTP_200_OK,
    response_model=BDAppsAckResponse,
    summary="BDApps SMS Delivery Status Report URL",
    description=(
        "Receives delivery status reports (`sms/report`) for SMS sent with "
        "`deliveryStatusRequest: \"1\"`. Log-only placeholder for now — no "
        "product requirement yet to persist delivery status per message."
    ),
)
def sms_report_callback(payload: SmsReportRequest):
    logger.info(
        "BDApps SMS delivery report: requestId=%s status=%s",
        payload.requestId,
        payload.deliveryStatus,
    )
    return BDAppsAckResponse()


@router.post(
    "/charging-notification",
    status_code=status.HTTP_200_OK,
    summary="BDApps CaaS Charging Notification URL (placeholder)",
    description=(
        "Receives charging (CaaS) notifications from BDApps. Configure this URL "
        "as the **Charging Notification URL** in the BDApps application "
        "configuration. Placeholder implementation — the BDApps TAP API "
        "documentation doesn't publish a payload schema for this callback "
        "(`caas/direct/debit` is synchronous, its own response is the "
        "result), so this accepts any payload and returns the documented "
        "ack; real parsing will be added once BDApps confirms the schema."
    ),
)
async def charging_notification_callback(request: Request):
    await _peek(request)
    return BDAppsAckResponse()


@router.post(
    "/subscription-notification",
    status_code=status.HTTP_200_OK,
    response_model=BDAppsAckResponse,
    summary="BDApps Subscription Notification URL",
    description=(
        "Receives subscription/un-subscription notifications from BDApps "
        "(`subscription/notify`). Configure this URL as the **Subscription "
        "Notification URL** in the BDApps application configuration. This "
        "is the only inbound BDApps callback that carries `applicationId`/"
        "`password`, so it's authenticated against our configured "
        "credentials before the subscriber's status is persisted."
    ),
)
def subscription_notification_callback(payload: SubscriptionNotifyRequest, db: Session = Depends(get_db)):
    if payload.applicationId != settings.bdapps_application_id or payload.password != settings.bdapps_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid application credentials")

    msisdn = normalize_msisdn(payload.subscriberId)
    now = datetime.now(timezone.utc)
    subscriber = db.query(BDAppsSubscriber).filter(BDAppsSubscriber.msisdn == msisdn).first()
    if subscriber is None:
        subscriber = BDAppsSubscriber(msisdn=msisdn, subscription_status=payload.status, last_event_at=now)
        db.add(subscriber)
    else:
        subscriber.subscription_status = payload.status
        subscriber.last_event_at = now
    db.commit()
    return BDAppsAckResponse()
