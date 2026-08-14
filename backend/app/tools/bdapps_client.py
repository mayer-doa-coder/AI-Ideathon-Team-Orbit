"""BDApps TAP API client — outbound calls the app makes to BDApps (`sms/send`,
`ussd/send`, `caas/get/balance`, `caas/direct/debit`, `subscription/send`,
`subscription/query-base`, `subscription/getStatus`).

Endpoint paths, field names, and the "S1000" success status code are exactly
what's documented at
https://dev.bdapps.com/API_Documentation/bdapps_tap_api.html — not invented.
Base URL and app credentials come from `Settings` (see `.env.example`).

BDApps requires calls to originate from a whitelisted IP. Render's own
outbound IP isn't static/whitelistable, so when `settings.fixie_url` is set
(Render's Fixie add-on, a static-outbound-IP HTTP proxy) every call is routed
through it instead of going out directly — otherwise BDApps rejects the
request with `E1303` regardless of valid credentials.

Every call raises `BDAppsAPIError` on transport failure or a non-"S1000"
`statusCode` from BDApps — callers must handle it explicitly rather than
treat a silent failure as success, same convention as `tools/weather.py`'s
`WeatherAPIError`.
"""
import httpx

from app.core.config import settings

REQUEST_TIMEOUT = 10.0


class BDAppsAPIError(Exception):
    """Raised when a BDApps TAP API call fails or returns a non-success statusCode."""


def normalize_msisdn(raw: str) -> str:
    """Normalize to the bare digits BDApps expects on subscriber addresses.

    BDApps requires the `880` country code with no leading `0` (e.g.
    `8801812345678`) — anything else fails direct_debit/etc. with `E1325`
    ("Format of the address is invalid. Expected format is tel:8801812345678").
    Farmers naturally type the local 11-digit form (`01812345678`), so that
    leading `0` is swapped for `880` here rather than pushing the format
    requirement onto every caller/the frontend.
    """
    digits = raw.strip().removeprefix("tel:").strip().lstrip("+")
    if digits.startswith("0"):
        digits = "880" + digits[1:]
    return digits


def _post(path: str, payload: dict) -> dict:
    url = f"{settings.bdapps_base_url}{path}"
    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            proxy=settings.fixie_url or None,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise BDAppsAPIError(f"BDApps call to {path} failed: {exc}") from exc

    status_code = data.get("statusCode")
    if status_code is not None and status_code != "S1000":
        raise BDAppsAPIError(f"BDApps {path} returned {status_code}: {data.get('statusDetail')}")
    return data


def send_sms(destination_msisdn: str, message: str, delivery_status_request: str = "0") -> dict:
    """POST /sms/send — send an MT SMS to a subscriber.

    Defaults to no delivery status report: this app's SMS SLA doesn't have
    that feature enabled, and requesting one (`"1"`) makes BDApps reject the
    whole send with `E1312` instead of just skipping the report."""
    return _post(
        "/sms/send",
        {
            "version": settings.bdapps_api_version,
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
            "message": message,
            "destinationAddresses": [f"tel:{normalize_msisdn(destination_msisdn)}"],
            "sourceAddress": settings.bdapps_sms_source_address,
            "deliveryStatusRequest": delivery_status_request,
        },
    )


def send_ussd(session_id: str, destination_msisdn: str, message: str, ussd_operation: str) -> dict:
    """POST /ussd/send — push USSD content to a subscriber.

    `ussd_operation` must be one of "mt-init", "mt-cont", "mt-fin".
    """
    return _post(
        "/ussd/send",
        {
            "version": settings.bdapps_api_version,
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
            "message": message,
            "sessionId": session_id,
            "ussdOperation": ussd_operation,
            "destinationAddress": f"tel:{normalize_msisdn(destination_msisdn)}",
            "encoding": "440",
        },
    )


def query_balance(subscriber_msisdn: str) -> dict:
    """POST /caas/get/balance — a subscriber's mobile-account balance/status."""
    return _post(
        "/caas/get/balance",
        {
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
            "subscriberId": normalize_msisdn(subscriber_msisdn),
            "paymentInstrumentName": "MobileAccount",
            "currency": "BDT",
        },
    )


def direct_debit(subscriber_msisdn: str, external_trx_id: str, amount: str, currency: str = "BDT") -> dict:
    """POST /caas/direct/debit — charge a subscriber's mobile account."""
    return _post(
        "/caas/direct/debit",
        {
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
            "externalTrxId": external_trx_id,
            "subscriberId": f"tel:{normalize_msisdn(subscriber_msisdn)}",
            "paymentInstrumentName": "MobileAccount",
            "amount": amount,
            "currency": currency,
        },
    )


def user_subscription(subscriber_msisdn: str, action: str) -> dict:
    """POST /subscription/send — subscribe ("1") or unsubscribe ("0") a subscriber."""
    return _post(
        "/subscription/send",
        {
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
            "subscriberId": f"tel:{normalize_msisdn(subscriber_msisdn)}",
            "action": action,
        },
    )


def base_size() -> dict:
    """POST /subscription/query-base — number of registered subscribers."""
    return _post(
        "/subscription/query-base",
        {
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
        },
    )


def subscriber_status(subscriber_msisdn: str) -> dict:
    """POST /subscription/getStatus — a subscriber's current subscription status."""
    return _post(
        "/subscription/getStatus",
        {
            "applicationId": settings.bdapps_application_id,
            "password": settings.bdapps_password,
            "subscriberId": f"tel:{normalize_msisdn(subscriber_msisdn)}",
        },
    )
