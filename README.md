# Green Leaf AI

An autonomous agricultural advisor for smallholder farmers in Bangladesh. It holds a conversation to learn a farm's specifics, calls real external services (weather, a knowledge base, market prices, disease identification) rather than inventing numbers, produces a costed and dated season plan, explains every recommendation in terms of the real data behind it, and keeps watching the forecast after the plan is made — proactively adjusting it when real weather threatens to waste an input.

Built for the IUT 12th ICT Fest — Bdapps Agentic AI Hackathon (Final Round), problem statement "Green Leaf AI."

**Live demo (frontend):** https://agrisense-frontend-4tkz.onrender.com

New to the project? [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) explains the whole thing in plain language, start to finish, before you get to the technical reference below.

---

## Table of contents

1. [What this is](#what-this-is)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [Tools and external APIs](#tools-and-external-apis)
5. [Feature coverage by tier](#feature-coverage-by-tier)
6. [Data: what is real and what is mock](#data-what-is-real-and-what-is-mock)
7. [Project structure](#project-structure)
8. [Setup](#setup)
9. [Running the test suite](#running-the-test-suite)
10. [Deployment](#deployment)
11. [Known limitations](#known-limitations)

---

## What this is

A farmer preparing for a new season has to make a chain of decisions — which crop, when to sow, how much fertilizer and water to budget, what pests to expect, whether the numbers leave any profit — using information that is real but scattered across weather services, soil guidelines, fertilizer charts, extension manuals, and market price boards, in formats that assume a specialist reader.

Green Leaf AI is built as two cooperating agents rather than a single chatbot:

- **The conversation agent** runs once per chat message (also reachable over SMS and USSD, not just the web). It gathers what is missing about the farm through targeted follow-up questions, retrieves grounded agronomic material and a real weather forecast, ranks candidate crops, produces a dated season plan, computes an itemized cost and profit projection, and answers open-ended farming questions — deciding for itself which of several tools a question actually needs.
- **The monitor agent** runs independently on a scheduled interval, in the background, for every farm with a committed plan. It re-checks the real forecast against the plan's pending fertilizer applications and upcoming pest/disease risk windows, and — deterministically, not by LLM guess — delays an application or flags a risk when the numbers say it should, then recomputes the financial impact and writes an alert.

Both agents are LangGraph graphs sharing the same Postgres database, so a change either one makes is immediately visible to the other and to the farmer's dashboard.

A full, plain-language walkthrough of every node in the conversation agent's graph is in [`CONVERSATION_AGENT_EXPLAINED.md`](CONVERSATION_AGENT_EXPLAINED.md); a rendered image of the actual compiled graph (generated directly from LangGraph, not hand-drawn) is [`conversation_agent_graph.png`](conversation_agent_graph.png).

---

## Architecture

```
                                   ┌─────────────────────────────┐
                                   │        React frontend        │
                                   │  (chat panel + live dashboard)│
                                   └───────────────┬───────────────┘
                                                    │ REST + Server-Sent Events
                                                    ▼
                                   ┌─────────────────────────────┐
                                   │        FastAPI gateway       │
                                   │  auth · chat · farms · monitor│
                                   │  alerts · trace · market ·    │
                                   │  rag · bdapps · payment       │
                                   └───────┬───────────────┬───────┘
                                           │               │
                          invokes per turn │               │ runs on a timer
                                           ▼               ▼
                          ┌───────────────────────┐  ┌───────────────────────┐
                          │   Conversation graph    │  │     Monitor graph      │
                          │   (LangGraph, per        │  │   (LangGraph, per      │
                          │   chat message)          │  │   scheduled sweep)     │
                          │                          │  │                        │
                          │  load_memory              │  │  fetch_weather          │
                          │  classify_intent           │  │  compare_thresholds      │
                          │  ask_followup / weather_tool│ │  recompute_season_plan   │
                          │  crop_recommendation         │ │  recompute_financials    │
                          │  season_planner                │  write_alert            │
                          │  calculate_financials            │                       │
                          │  qa_agent · scenario_handler       │                     │
                          │  disease_detection · marketplace_lookup                  │
                          │  market_price_lookup · persist                          │
                          └───────────┬───────────────┘  └───────────┬───────────┘
                                      │                               │
                                      ▼                               ▼
                          ┌───────────────────────────────────────────────────┐
                          │                    PostgreSQL + pgvector            │
                          │  users · farms · plans · alerts · trace_log ·       │
                          │  kb_chunks (vector) · market_prices · suppliers ·    │
                          │  supplier_products · bdapps_subscribers ·            │
                          │  bdapps_charge_transactions ·                        │
                          │  LangGraph checkpoint tables (conversation memory)   │
                          └───────────────────────┬─────────────────────────────┘
                                                   │
                     ┌─────────────────────────────┼──────────────────────────────────┐
                     ▼                             ▼                                  ▼
            Open-Meteo (weather +          OpenAI API (chat +             Kindwise crop.health,
            geocoding, keyless)            embeddings)                    Tavily, BDApps TAP API,
                                                                           Bangladesh DAM (scraped)
```

**Two kinds of memory, deliberately kept separate:**

- A **LangGraph Postgres checkpointer** holds each conversation's short-term state (message history, in-progress profile, trace log), keyed by user id (or MSISDN for SMS/USSD).
- The **relational domain tables** (`farms`, `plans`, `alerts`, ...) are the durable record. Every conversation turn re-reads them at its start, specifically because the monitor agent writes to `plans` directly, independent of any chat turn — this is how a monitor-triggered adjustment (made while the farmer wasn't even in the app) reaches the next chat message and the dashboard on the very next page load.

**Streaming:** the chat endpoint (`POST /api/chat`) streams the conversation graph's execution live over Server-Sent Events — tokens, tool-call trace entries, weather/crop/plan/financial updates — so the dashboard updates incrementally in the same turn a multi-step chain (weather → crop ideas → season plan → financials) runs, rather than waiting for one final response.

**Scheduler:** an in-process APScheduler job (no separate worker/broker service) sweeps every farm with a committed plan through the monitor graph on a fixed interval, configurable via `MONITOR_INTERVAL_HOURS`.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, React Router 7 |
| 3D avatar | react-three-fiber, @react-three/drei, Three.js (renders a Mixamo character; idle presence only today — no live speech/TTS wired in yet) |
| Backend API | FastAPI, Uvicorn, Pydantic v2 / pydantic-settings |
| Agent orchestration | LangGraph (two graphs — conversation and monitor), LangChain, langchain-openai |
| LLM | OpenAI API — chat/reasoning model and a separate vision call for disease cross-verification |
| Embeddings | OpenAI `text-embedding-3-small` |
| Database | PostgreSQL 16 with the `pgvector` extension |
| ORM / migrations | SQLAlchemy, Alembic |
| Conversation memory | `langgraph-checkpoint-postgres` (psycopg3 connection pool) |
| Relational access | SQLAlchemy over psycopg2 |
| Background jobs | APScheduler (`AsyncIOScheduler`), in-process |
| Auth | JWT (`python-jose`), `bcrypt` password hashing |
| HTTP client | `httpx` |
| PDF ingestion | `pypdf` |
| HTML scraping | `beautifulsoup4` (Bangladesh DAM market-price report) |
| Disease identification SDK | `kindwise-api-client` |
| Testing | `pytest` |
| Containerization | Docker, Docker Compose (Postgres + backend + frontend) |
| Hosting | Render (Blueprint: managed Postgres, a Python web service for the backend, a static site for the frontend) |

---

## Tools and external APIs

| Tool / API | Used for | Real or mock | Auth required |
|---|---|---|---|
| Open-Meteo Geocoding + Forecast API | Resolving a place name to coordinates and fetching a real 14-day rainfall/temperature forecast | Real, live, keyless | No |
| OpenAI API (chat/reasoning model) | Intent classification, crop ranking, season-plan generation, general Q&A tool selection, casual replies, scenario re-planning | Real, live | Yes (API key) |
| OpenAI API (`text-embedding-3-small`) | Embedding the knowledge base and search queries for retrieval | Real, live | Yes (API key) |
| OpenAI API (vision call) | A second, independent look at an uploaded leaf photo to confirm or challenge the disease classifier's top candidate | Real, live | Yes (API key) |
| Kindwise crop.health API | Real plant disease identification from an uploaded photo (top-3 candidates with confidence and treatment text) | Real, live (credit-metered) | Yes (API key) |
| Tavily Search API | Web-search fallback, used only when the knowledge base has nothing relevant for a query | Real, live | Yes (API key) |
| Bangladesh Department of Agricultural Marketing (DAM) | Current and historical crop prices, ingested offline (DAM has no documented public API — its real commodity-price report is a CSRF-protected HTML form, submitted for real by an ingestion script, not called live inside a request) | Real data, ingested in advance | No key (session/CSRF handled by the ingestion script) |
| BDApps TAP API | SMS and USSD access to the same conversation agent, and a CaaS ("Charging as a Service") direct-debit checkout flow — see [`BDAPPS_INTEGRATION.md`](BDAPPS_INTEGRATION.md) for the full walkthrough | Real integration, sandbox credentials | Yes (application id/password) |
| PostgreSQL + pgvector | Knowledge-base similarity search, all relational storage, and the LangGraph checkpoint tables | Real, self-hosted / managed | — |

---

## Feature coverage by tier

Mapped against the hackathon's own tier definitions.

### Tier 0 — Core (required)

| # | Capability | Status | Where |
|---|---|---|---|
| 1 | Conversational intake (location, farm size, soil, water, budget, season; targeted follow-ups only for what's missing) | Done | `nodes/classify_intent.py`, `nodes/ask_followup.py` |
| 2 | Live weather grounding, real API, no invented forecasts | Done | `nodes/weather_tool.py`, `tools/weather.py` |
| 3 | Crop recommendation, at least 3 ranked candidates with suitability/water need/risk/profit | Done | `nodes/crop_recommendation.py` |
| 4 | Dated season plan (sowing, fertilizer, irrigation, weed/pest checkpoints, harvest) | Done | `nodes/season_planner.py` |
| 5 | Itemized, internally consistent financial projection (cost, revenue, profit, ROI, break-even) | Done | `nodes/calculate_financials.py`, `tools/financials.py` (pure function, no LLM) |
| 6 | Explained reasoning naming the specific inputs behind each recommendation | Done | `reasoning` field on every plan/candidate; `qa_agent` cites its tool calls |
| 7 | Knowledge base with RAG, grounding crop/fertilizer/season-plan advice | Done | `pgvector`, four ingested public reference documents (see below) |
| 8 | Visible agent trace — every tool call, its parameters, and the raw result | Done | `trace_log` on every graph node, streamed live over SSE and also persisted (`GET /api/trace/{farm_id}`) |

### Tier 1 — Advanced

See [`TIER_1_FEATURES.md`](TIER_1_FEATURES.md) for a plain-language explanation of how each of these actually works.

| Capability | Status | Notes |
|---|---|---|
| Persistent memory across sessions | Done | Farm/plan state in relational tables; conversation history in the LangGraph Postgres checkpointer — both survive a logout/login |
| Proactive, weather-triggered plan adjustment | Done | The monitor agent (`graph_monitor.py`) runs on a schedule, independent of the chat, and writes adjustments straight to the committed plan |
| Fertilizer and irrigation scheduler, tied to crop/soil, with cost | Done | Quantities, per-stage timing, and cost are real and computed; an "organic alternative" field exists in the data shape but is not currently populated by the model — always empty today |
| Pest and disease risk prediction (crop + growth stage + weather), with prevention and cost | Mostly done | Risk windows are grounded in retrieved crop-specific material and the real forecast, and reactively escalated by the monitor agent; cost is captured as one aggregate "Pest & Disease Control" line in the budget rather than an itemized figure per predicted pest, and there is a single `prevention` field reused for both prevention and post-outbreak guidance rather than two distinct fields |
| Scenario simulation ("what if...") | Done | Both a pure narration mode and a mode that actually regenerates and commits a revised, re-costed plan; a rainfall-only "apply this" is deliberately refused (see Known limitations) |

### Tier 2 — Ambitious (bonus)

| Capability | Status | Notes |
|---|---|---|
| Marketplace and supplier comparison | Not done (placeholder) | Not currently functional |
| Market price intelligence with a sell/store/wait verdict | Not done (placeholder) | Not currently functional |
| Plant disease detection from an uploaded photo | Done | Kindwise crop.health plus an independent OpenAI vision cross-check; a diagnosis is only reported as high-confidence when both agree, and nothing is fabricated when either call fails |
| BDApps Payment Gateway integration | Not done (placeholder) | Not currently functional |
| Bengali language UI | Done | Full English/Bangla toggle across the chat UI, dashboard, and site pages |
| Voice interaction | Not done | Voice input/output UI is present but disabled; not currently functional |

---

## Data: what is real and what is mock

**Real, live, or ingested-from-a-real-source:**

- **Weather** — every forecast shown or acted on comes from a real Open-Meteo API call. Because Open-Meteo's own place-name gazetteer has confirmed gaps for Bangladesh (e.g. it silently resolves "Bogura" to an unrelated location in Russia, and doesn't recognize "Cumilla" at all), district-level lookups are first checked against a hardcoded, cross-verified table of all 64 Bangladeshi districts' real coordinates before falling back to the live geocoder for anything more specific.
- **Knowledge base** — grounded in four real, publicly available Bangladesh agriculture references, embedded and stored in `pgvector`: BARC's *Hand Book of Agricultural Technology* (2013, 862 chunks), the *Fertilizer Recommendation Guide* (2018, BARC), the *Soil Fertility Atlas Bangladesh* (2020 extract), and the *Yearbook of Agricultural Statistics* (2020, Chapter 1 — Agro-Ecological Zones, soil classification, crop calendar).
- **Web search fallback** — real Tavily results, only invoked when the knowledge base has nothing relevant, and always clearly labeled with a real source URL wherever it surfaces.
- **Market prices** — real observations from the Bangladesh Department of Agricultural Marketing, ingested by a script that submits DAM's own (undocumented, CSRF-protected) commodity report form for real and writes the result to Postgres. Genuinely missing coverage is reported as "insufficient data," never invented.
- **Plant disease identification** — a real Kindwise crop.health API call on every uploaded photo, cross-checked by a second, independent vision call; if either call fails, no diagnosis is fabricated to fill the gap.
- **BDApps integration** — real API calls against the BDApps TAP API (SMS, USSD, and CaaS direct-debit) in sandbox mode, with every charge attempt recorded as a receipt regardless of outcome.

**Generated by the LLM, grounded in the above (not invented from nowhere, but not "real-world observed" either):**

- Crop rankings, the specific dated season-plan calendar, and the natural-language reasoning text — all produced by the LLM, but only ever from the retrieved knowledge-base material and the real forecast passed into the same prompt, never from unstated general knowledge (enforced both by prompt instructions and, for the general Q&A agent, by requiring an actual tool call before any checkable fact is stated).

**Mock / static / illustrative — clearly not a live feed:**

- The **cost and yield reference constants** in `tools/financials.py` (fertilizer BDT/kg, seed BDT/kg, land preparation/irrigation/pest-control/labor/post-harvest cost per acre, and market price per ton by crop) are static, illustrative Bangladesh smallholder reference figures used to price the season plan's cost/profit projection. This is separate from — and not fed by — the real DAM price data, which powers the standalone Market Price Intelligence ("should I sell now?") feature instead.
- The **supplier/marketplace catalog** (`suppliers`, `supplier_products`) is a seeded, realistically-designed mock dataset (price levels anchored to the real fertilizer reference prices above, uneven ratings/stock/delivery, one deliberately out-of-stock listing, one deliberately stale one) — explicitly the "seeded or mock supplier catalog" the brief allows, not a live supplier feed.

---

## Project structure

```
Green Leaf-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                    FastAPI app, CORS, router registration, scheduler lifespan
│   │   ├── core/                      settings (pydantic-settings), password hashing, JWT
│   │   ├── db/                        SQLAlchemy engine/session, models, trace_log helper
│   │   ├── models/                    SQLAlchemy user model
│   │   ├── schemas/                   Pydantic request/response schemas
│   │   ├── services/                  DB access kept out of route handlers
│   │   ├── api/routes/                auth, chat, farms, monitor, alerts, trace, market, rag, bdapps, payment
│   │   ├── tools/                     weather, financials, market_price, market_analytics, market_decision,
│   │   │                              marketplace, crop_health, web_search, bdapps_client
│   │   ├── rag/                       ingestion + retrieval + per-document loaders for the knowledge base
│   │   └── agents/
│   │       ├── state.py               shared AgentState / MonitorState / SeasonPlan schemas
│   │       ├── graph_conversation.py  builds and compiles the conversation graph
│   │       ├── graph_monitor.py       builds and compiles the monitor graph, run_monitor_sweep()
│   │       ├── router.py              conditional-edge routing logic for the conversation graph
│   │       ├── checkpointer.py        LangGraph Postgres checkpointer
│   │       ├── nodes/                 every conversation-graph node
│   │       ├── monitor_nodes/         every monitor-graph node
│   │       └── prompts/               system prompts (markdown) for each LLM-backed node
│   ├── scripts/                       knowledge-base ingestion, DAM price ingestion, supplier seeding, demo-farm seeding
│   ├── tests/                         pytest suite
│   └── alembic/                       database migrations
├── frontend/
│   └── src/
│       ├── pages/                     HomePage, LoginPage, ChatPage (the live dashboard)
│       ├── components/                chat UI, dashboard panels (trace log, weather, crop comparison,
│       │                              season timeline, financial breakdown, alerts feed), 3D avatar
│       ├── services/                  fetch wrappers for every backend route group
│       └── context/                   auth state
├── docker-compose.yml                 Postgres + backend + frontend, for local development
├── render.yaml                        Render Blueprint used for the hosted deployment
├── CONVERSATION_AGENT_EXPLAINED.md    full plain-language walkthrough of the conversation graph
└── conversation_agent_graph.png       the compiled conversation graph, rendered by LangGraph itself
```

---

## Setup

### Prerequisites

- Python 3.11+ (Render deploys on 3.13)
- Node.js 18+
- Docker Desktop (or Docker Engine + Compose v2) — only needed for the Docker path
- API keys: OpenAI (required for the agents to run), Kindwise crop.health, Tavily (optional — enables the web-search fallback), BDApps application credentials (optional — enables SMS/USSD/payment)

### Option A — Docker (recommended, runs everything)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Fill in `backend/.env`: at minimum `OPENAI_API_KEY` and a generated `JWT_SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). `DATABASE_URL` inside `backend/.env` only matters when running the backend outside Docker — `docker-compose.yml` overrides it to point at the containerized Postgres.

```bash
docker compose up -d --build
```

This starts three containers:

- **postgres** — Postgres 16 with `pgvector`, published on host port `5433` (5432 is left free for a native install), data persisted in a named volume.
- **backend** — FastAPI on `http://localhost:8000`. Runs `alembic upgrade head` on start, then Uvicorn, after waiting for Postgres's healthcheck.
- **frontend** — Vite dev server on `http://localhost:5173`, talking to the backend on `http://localhost:8000`.

```bash
docker compose ps
docker compose logs -f backend
docker compose down          # stop, keep the Postgres volume
docker compose down -v       # stop and also delete the Postgres volume
```

### Option B — Run each service manually

**Database** (still easiest via Docker, just the one service):

```bash
docker compose up -d postgres
```

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows; source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env               # fill in DATABASE_URL, OPENAI_API_KEY, JWT_SECRET_KEY, etc.
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API is now at `http://localhost:8000`; interactive docs at `http://localhost:8000/docs`.

**Frontend:**

```bash
cd frontend
npm install
cp .env.example .env               # set VITE_API_URL if the backend isn't on the default port
npm run dev
```

Opens at `http://localhost:5173`.

### Populating real data

The app runs with an empty knowledge base and no market/supplier data by default. To populate it:

```bash
cd backend
python -m scripts.run_ingestion               # BARC Hand Book of Agricultural Technology
python -m scripts.ingest_frg_2018              # Fertilizer Recommendation Guide 2018
python -m scripts.ingest_soil_fertility_atlas  # Soil Fertility Atlas Bangladesh 2020
python -m scripts.ingest_yearbook_chapter1     # Yearbook of Agricultural Statistics 2020, Ch.1
python -m scripts.ingest_market_prices         # real DAM price history (several minutes; DAM is slow)
python -m scripts.seed_suppliers               # seeded/mock marketplace catalog
python -m scripts.seed_demo_farm               # optional: a ready-made demo farm + committed plan,
                                                # for exercising the monitor agent without onboarding first
```

### Key environment variables (backend)

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string |
| `OPENAI_API_KEY` | Yes | Chat, embeddings, and vision calls |
| `JWT_SECRET_KEY` | Yes | Signs auth tokens |
| `CROP_HEALTH_API_KEY` | For disease detection | Kindwise crop.health |
| `TAVILY_API_KEY` | For web-search fallback | Tavily Search API |
| `MONITOR_INTERVAL_HOURS` | No (default set in code) | How often the monitor agent sweeps every farm |
| `CORS_ORIGINS` | Yes in production | Comma-separated allowed frontend origins |
| `BDAPPS_APPLICATION_ID` / `BDAPPS_PASSWORD` | For BDApps SMS/USSD/payment | BDApps TAP API application credentials |
| `BDAPPS_BASE_URL` / `BDAPPS_API_VERSION` | No (defaults set) | BDApps TAP API endpoint configuration |
| `FIXIE_URL` | No | Optional static-outbound-IP proxy, needed only if BDApps requires calls from a whitelisted IP that the hosting platform doesn't provide by default |

---

## Running the test suite

```bash
cd backend
pytest
```

Covers, among other things: the deterministic financial calculator, the market-price trend/decision engine (including a case where season alone flips the sell/store/wait verdict), the monitor agent's threshold comparison logic, the router's conditional-edge decisions, and the core-profile-change handler.

### Adding a new database model

New SQLAlchemy models need an Alembic migration:

```bash
cd backend
alembic revision --autogenerate -m "..."
alembic upgrade head
```

---

## Deployment

Deployed via the Render Blueprint at [`render.yaml`](render.yaml):

- **agrisense-postgres** — a managed Postgres database (Singapore region).
- **agrisense-backend** — the FastAPI app as a native Python web service; build runs `pip install -r requirements.txt`, start runs `alembic upgrade head` followed by Uvicorn.
- **agrisense-frontend** — the Vite/React app built as a static site (`npm ci && npm run build`), with all routes rewritten to `index.html` for client-side routing.


---

## Known limitations

Documented here rather than glossed over, in the same spirit as the rest of this README:

- The season plan's financial projection is priced from static reference constants, not a live market feed (see [Data](#data-what-is-real-and-what-is-mock) above) — the separate Market Price Intelligence feature is what carries real, current prices.
- A scenario ("what if") request that is both rainfall-driven and asks to actually apply the change is deliberately refused rather than simulated, because there is only one real forecast per location, not a rainfall simulator; the farmer is pointed at the monitor agent instead, which reacts to the real forecast automatically.
- The "organic alternative" field in the season-plan data shape is not currently populated.
- Pest/disease cost is one aggregate line in the budget, not an itemized figure per predicted risk; "treatment" and "prevention" currently share a single field rather than being tracked separately.
- Bengali-language UI is done (a full English/Bangla toggle), but voice/TTS interaction is not — the voice UI exists but is currently disabled. The 3D avatar's mouth-movement logic is real and frame-accurate, but has no live speech input to react to today.
- The BDApps charging-notification webhook is a placeholder ack — BDApps' own TAP API documentation does not publish a payload schema for it, since `caas/direct/debit` is a synchronous call whose own response is already the result.
