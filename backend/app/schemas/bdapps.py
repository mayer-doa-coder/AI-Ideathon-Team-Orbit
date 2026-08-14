"""Request/response schemas for the BDApps TAP API callback contract.

Field names/types mirror the BDApps TAP API documentation
(https://dev.bdapps.com/API_Documentation/bdapps_tap_api.html) exactly —
these are what BDApps actually POSTs to our registered callback URLs, not an
internal shape we chose.
"""
from pydantic import BaseModel


class BDAppsAckResponse(BaseModel):
    """The documented ack shape every inbound BDApps callback expects back."""

    statusCode: str = "S1000"
    statusDetail: str = "Success."


class UssdReceiveRequest(BaseModel):
    version: str
    applicationId: str
    message: str
    requestId: str
    sessionId: str
    ussdOperation: str
    sourceAddress: str
    vlrAddress: str | None = None
    encoding: str


class SmsReceiveRequest(BaseModel):
    version: str
    applicationId: str
    sourceAddress: str
    message: str
    requestId: str
    encoding: str


class SmsReportRequest(BaseModel):
    destinationAddress: str
    timeStamp: str
    requestId: str
    deliveryStatus: str


class SubscriptionNotifyRequest(BaseModel):
    timeStamp: str
    version: str
    applicationId: str
    password: str
    subscriberId: str
    frequency: str
    status: str
