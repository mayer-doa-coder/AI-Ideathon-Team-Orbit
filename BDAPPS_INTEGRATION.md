# How BDApps is integrated in Green Leaf AI

BDApps is a Bangladeshi telecom platform that lets a registered application send and
receive SMS, run USSD sessions, and charge a subscriber's mobile account directly —
all without the person needing a smartphone, an app install, or even internet access.
This document explains exactly how Green Leaf AI plugs into it: what BDApps sends us,
what we send back, and where each piece lives in the code.

For the plain-language "what is this project" version, see
[`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md). For the technical reference tables
(status of every feature, env vars, tech stack), see [`README.md`](README.md).

---

## 1. Why it's here

Everything else in this app — the web chat, the dashboard — assumes the farmer has a
smartphone and a data connection. A lot of smallholder farmers in Bangladesh don't.
BDApps is what closes that gap: it gives the *exact same conversation agent* a second
and third front door — a plain SMS and a USSD menu — that work on any basic phone.

---

## 2. The two directions of communication

BDApps talks to this app in two directions, and the code is split the same way:

- **Inbound — BDApps calls us.** These are "callback URLs" you register once in the
  BDApps developer portal. Every time a farmer texts something, dials the USSD code,
  or (un)subscribes, BDApps sends an HTTP POST to one of our registered endpoints.
  This side lives in **`backend/app/api/routes/bdapps.py`**.
- **Outbound — we call BDApps.** To actually reply (send an SMS, push USSD content,
  charge a subscriber), our server makes its own POST requests to BDApps' API. This
  side lives in **`backend/app/tools/bdapps_client.py`**.

The request/response shapes for both directions are defined in
**`backend/app/schemas/bdapps.py`**, and every field name, endpoint path, and the
`"S1000"` success code are copied exactly from BDApps' own TAP API documentation —
nothing here is guessed.

---

## 3. Walking through an SMS conversation

1. A farmer texts a keyword plus their question to a shortcode BDApps has assigned
   this app (e.g. `AGRI what fertilizer does rice need`).
2. BDApps POSTs that message to our **`/api/bdapps/sms`** callback.
3. The handler strips the routing keyword off the front (so the agent sees just the
   real question), then hands it straight to the **same LangGraph conversation agent**
   that powers the web chat — keyed by the farmer's phone number instead of a login
   account.
4. Whatever the agent replies gets sent back for real via `bdapps_client.send_sms()`,
   which calls BDApps' `/sms/send` endpoint.
5. If the farmer requested a delivery report, a separate callback
   (`/api/bdapps/sms-delivery-report`) receives BDApps' confirmation of whether the
   text actually reached the phone. Right now this is logged only — nothing yet reads
   it back out.

## 4. Walking through a USSD session

USSD is different: it's a live, short-lived interactive session (like the on-screen
menus used for mobile banking), not a one-off text.

1. The farmer dials the USSD code. BDApps opens a session and POSTs an `mo-init`
   event to **`/api/bdapps/ussd`**.
2. The app immediately pushes back a prompt ("Type your farming question:") via
   `bdapps_client.send_ussd(..., "mt-cont")` — `mt-cont` keeps the session open,
   waiting for the next screen of input.
3. The farmer types their question; BDApps sends that as an `mo-cont` event to the
   same callback.
4. This time the message goes to the conversation agent for a real answer. Because a
   phone screen can only show so much, the reply is trimmed to a safe character limit
   before being sent back — never silently cut off mid-word by the carrier instead.
5. The reply goes out via `send_ussd(..., "mt-fin")` — `mt-fin` closes the session.
   USSD here is single-turn: one question, one answer, done.

## 5. Keeping track of who's subscribed

Whenever someone subscribes or unsubscribes from the service, BDApps notifies
**`/api/bdapps/subscription-notification`**. This is the *only* inbound callback that
carries the app's own `applicationId`/`password`, so it's the one place we can
actually verify a callback genuinely came from BDApps and not somewhere else — the
handler checks those credentials before writing anything. Confirmed subscribers are
stored in the `BDAppsSubscriber` table, keyed by phone number.

(Worth noting: this app's BDApps configuration currently has "Subscription Required"
set to **NO** for both SMS and USSD, so a farmer gets an answer whether or not they've
formally subscribed — the subscription table exists and is kept accurate, but it isn't
currently used as a gate.)

## 6. Payments (CaaS — Charging as a Service)

BDApps also supports billing a subscriber directly through their phone account
instead of a card. This app's checkout flow (**`backend/app/api/routes/payment.py`**)
really does call BDApps' real `/caas/direct/debit` endpoint via
`bdapps_client.direct_debit()`, in sandbox mode, with a generated transaction ID.

What makes this honestly-built rather than just a fake "success" screen: **every
attempt is recorded, whether it succeeds or fails.** A `BDAppsChargeTransaction` row
gets written either way — a rejected charge is just as visible in the receipt history
as a successful one, never silently dropped.

The one piece that stays a placeholder: BDApps' own API documentation doesn't publish
a payload schema for the asynchronous charging-notification webhook
(`/api/bdapps/charging-notification`) — because `direct/debit` is actually a
*synchronous* call whose own HTTP response already tells you the result, BDApps' docs
don't specify what (if anything) shows up on that webhook afterward. So that one
endpoint just accepts whatever it's sent and acknowledges it, without trying to parse
a schema nobody has documented.

For the current overall status of the payment feature (real code vs. what's actually
verified working end to end), see the "Feature coverage by tier" table in
[`README.md`](README.md) — treat that table as the source of truth if it ever seems to
disagree with this description of the code.

## 7. A deployment quirk worth knowing

BDApps only accepts API calls from an IP address that's been specifically
pre-approved ("whitelisted") for this application. Render's servers don't have a
fixed outbound IP by default, so every outbound BDApps call in `bdapps_client.py` is
routed through a static-IP proxy (Render's Fixie add-on) whenever one is configured —
otherwise BDApps rejects every request with an `E1303` error regardless of whether the
credentials are correct.

---

## 8. Where everything lives

| Piece | File |
|---|---|
| Inbound callbacks (SMS, USSD, subscription, charging notification) | `backend/app/api/routes/bdapps.py` |
| Outbound API client (send SMS, push USSD, direct debit, subscription queries) | `backend/app/tools/bdapps_client.py` |
| Request/response shapes matching BDApps' own docs | `backend/app/schemas/bdapps.py` |
| Payment checkout built on top of the CaaS client | `backend/app/api/routes/payment.py` |
| Subscriber record | `backend/app/db/models.py` (`BDAppsSubscriber`) |
| Charge/receipt record | `backend/app/db/models.py` (`BDAppsChargeTransaction`) |
| Config (application ID, password, base URL, proxy) | `backend/app/core/config.py`, set via `BDAPPS_*` / `FIXIE_URL` env vars |

## 9. Configuration needed to turn this on

All optional — the rest of the app works without them, this integration just won't:

| Env var | What it's for |
|---|---|
| `BDAPPS_APPLICATION_ID` / `BDAPPS_PASSWORD` | Credentials issued when you register the app in the BDApps portal |
| `BDAPPS_SMS_SOURCE_ADDRESS` | The shortcode SMS replies appear to come from |
| `BDAPPS_BASE_URL` / `BDAPPS_API_VERSION` | BDApps TAP API endpoint + version (defaults already set) |
| `FIXIE_URL` | Static-outbound-IP proxy, only needed if your host's IP isn't already whitelisted with BDApps |

And in the BDApps portal itself, this app's callback URLs need to be pointed at:
`/api/bdapps/ussd`, `/api/bdapps/sms`, `/api/bdapps/sms-delivery-report`,
`/api/bdapps/subscription-notification`, and `/api/bdapps/charging-notification`.
