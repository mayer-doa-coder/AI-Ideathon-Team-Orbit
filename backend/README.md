# AgriSense AI — Backend

FastAPI backend for AgriSense AI. Real, working pieces so far: **user authentication** (register/login/JWT), the **RAG knowledge base** (pgvector + `text-embedding-3-small` over the BARC agricultural handbook), and the **monitor agent** (a LangGraph graph that watches a real weather forecast and proactively adjusts a farm's season plan). The conversational **onboarding / crop recommendation / season planning** flow the chat UI shows is still simulated on the frontend — that's the conversation agent's separate, in-progress piece.

## Setup

```powershell
cd backend
python -m venv venv          # if not already created
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in real values (`DATABASE_URL`, `JWT_SECRET_KEY`, `OPENAI_API_KEY`). A `JWT_SECRET_KEY` should be a long random string — e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Database

Postgres runs via the root `docker-compose.yml` on **port 5433** (not 5432 — this machine has a native Postgres install already using 5432; see `DATABASE_URL` in `.env`):

```bash
docker compose up -d postgres   # from the repo root
```

Apply migrations:

```powershell
alembic upgrade head
```

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

API available at http://localhost:8000. CORS is configured to allow the frontend dev server at http://localhost:5173.

## Run with Docker

See the [root README](../README.md#run-everything-with-docker) — `docker compose up -d --build` from the repo root builds and runs Postgres, this API, and the frontend together. The backend's `Dockerfile` runs `alembic upgrade head` on container start before launching Uvicorn.

## Auth endpoints

- `POST /api/auth/register` — `{ username, password }` → `{ access_token, token_type, username }` (auto-logs in)
- `POST /api/auth/login` — form-encoded `username`/`password` → same `Token` shape
- `GET /api/auth/me` — requires `Authorization: Bearer <token>` → `{ id, username }`

## RAG endpoints

- `POST /api/rag/search` — `{ query, crop?, topic?, k? }` → top-k `kb_chunks` by cosine similarity, no LLM call
- `POST /api/rag/ask` — `{ query, k? }` → LLM answer grounded only in retrieved chunks, plus its sources

Knowledge base: 862 chunks from BARC's *Hand Book of Agricultural Technology* (2013), chunked by crop/topic heading and embedded with `text-embedding-3-small`. Rebuild with `python -m scripts.run_ingestion`.

## Monitor agent

A LangGraph graph (`app/agents/graph_monitor.py`) that watches one farm's committed season plan against a real weather forecast and proactively delays/flags items before they cause a real loss — e.g. delaying a fertilizer application ahead of forecast heavy rain (runoff risk), or flagging a pest/disease risk window when rain conditions favor it. All threshold/adjustment logic (`app/agents/monitor_nodes/`) is deterministic Python, not an LLM call — reproducible and inspectable, which is what makes the financial recompute after an adjustment trustworthy.

**Real:** the weather forecast (Open-Meteo, keyless, no invented values), the threshold comparison and plan/financials recompute, the persisted `alerts` + `trace_log` rows (so a farmer's history survives across logins), and the in-process APScheduler sweep (every `MONITOR_INTERVAL_HOURS`, default 6, over every farm with `is_active = true`).
**Mock / reference data, not live:** the crop cost/yield/market-price constants in `app/tools/financials.py` are static illustrative figures for Bangladesh smallholder farming, used for the season-plan cost/profit estimate — not a live market feed. For real, current market prices see **Market Price Intelligence** below.

Endpoints (all require `Authorization: Bearer <token>`, and the farm must belong to the caller):

- `POST /api/monitor/check-weather-now/{farm_id}` — real Open-Meteo call, runs the actual graph
- `POST /api/monitor/simulate-trigger/{farm_id}` — same graph, but with a synthetic heavy-rain forecast injected instead of a real API call, so a trigger can be demoed on demand; the response and UI both label this as simulated, not live weather
- `GET /api/alerts?farm_id=` / `POST /api/alerts/{id}/read` — a farm's persisted alert history
- `GET /api/trace/{farm_id}` — every tool call any graph made for that farm (tool name, params, raw result, timestamp) — the "visible agent trace" judges can use to confirm a number came from a real call
- `GET /api/farms/me` — the caller's active farm (404 if none yet)

There's no UI flow yet to create a farm from scratch (that's the conversation agent's onboarding job). To exercise the monitor agent standalone:

```powershell
python -m scripts.seed_demo_farm   # creates user "demo_farmer" / a Rajshahi rice farm / a committed season plan
```

It prints the farm id and the exact `curl`/endpoint calls to try next.

## Market Price Intelligence

Answers "should I sell my rice now?" using **real** crop prices from the Bangladesh Department of Agricultural Marketing (DAM, `market.dam.gov.bd`) and a deterministic SELL NOW / STORE / WAIT decision engine — never an LLM guess.

**DAM has no documented public API.** This was confirmed by direct inspection, not assumed: their real data lives behind a CSRF-protected HTML report form (`commodity_wise_report`), which `app/tools/market_price.py` submits for real (session + CSRF token handling, no invented endpoint). Two real, load-bearing constraints this drove:

- DAM's report is a **period aggregate** (min/max/avg over a date range you choose), not a daily series export, and their server takes ~20-30s per query. Ingestion is therefore a **standalone script that writes to Postgres**, never a live call inside a chat turn or API request — every route/agent node reads what was already ingested.
- Coverage is genuinely sparse (many commodity/market/period combinations have nothing on file — DAM's own site says so). Every layer of this feature is built to say "insufficient data" honestly rather than fabricate a number — this is required behavior, not a fallback for a bug.

**Real:** all prices, ingested via `python -m scripts.ingest_market_prices` (optionally `--crops onion,potato` to scope a run — a full run across all 9 mapped crops takes several minutes given DAM's response time). Maps to 9 of `financials.py`'s 10 canonical crops (**lentil has no DAM commodity at all** — confirmed by exhaustively searching DAM's 434-item commodity list, not a lookup gap — so lentil market intelligence always reports unavailable). Rice is split by growing season (Aus/Aman/Boro are genuinely different commodities with different prices) — this is also how "season" concretely changes which real data gets fetched, not just a decision-engine weight.
**Deterministic, not LLM-decided:** `app/tools/market_decision.py` is a transparent weighted-factor scorer (price vs. historical average, trend, proximity to historical high/low, season vs. harvest season, urgent cash need, storage availability/cost) that always produces exactly one of `SELL_NOW` / `STORE` / `WAIT`, or `None` when there isn't enough real data to ground a decision in — every factor that fires appends a plain-language reason (`decision.reasons`), so the verdict is always explainable.

Endpoints (all require `Authorization: Bearer <token>`):

- `GET /api/market/crops` — the crops market intelligence has a DAM mapping for
- `GET /api/market/current?crop=&season=&district=` — current price + historical average/high/low/trend
- `GET /api/market/history?crop=&season=&district=&days=` — raw ingested observations, for charting
- `GET /api/market/decision?crop=&season=&district=&storage_available=&storage_cost_bdt_per_unit_per_month=&quantity_kg=&urgent_cash_needed=` — snapshot + verdict + reasons (what the dashboard card and agent both call)

In the chat agent, ask things like *"should I sell my potato now?"* or *"is this a good time to sell onion?"* — `classify_intent` extracts the crop/quantity/storage/urgency, `agents/nodes/market_price_lookup.py` retrieves the real snapshot and runs the decision engine, and emits four separate trace entries (current price, historical prices, trend analysis, decision result) to the live agent trace. Crop recommendations (`crop_recommendation.py`) also get this attached automatically per-candidate, best-effort — a market-data gap never breaks the recommendation itself.

Tests: `python -m pytest tests/test_market_analytics.py tests/test_market_decision.py -v` — retrieval, trend calculation, all three verdicts, season explicitly (including a case where season alone flips the verdict), and insufficient/missing data handling.

## Structure

```
app/
├── main.py                # FastAPI app, CORS, routers, scheduler lifespan
├── core/                   # settings, password hashing, JWT
├── db/                      # SQLAlchemy engine/session, models, trace_log helper
├── models/                    # SQLAlchemy models (users)
├── schemas/                    # Pydantic request/response schemas
├── services/                    # DB access, kept out of route handlers
├── api/routes/                   # route handlers (auth, rag, farms, monitor, alerts, trace, market)
├── tools/                         # weather.py (Open-Meteo), financials.py (deterministic calc),
│                                     market_price.py (DAM client), market_analytics.py,
│                                     market_decision.py (deterministic sell/store/wait)
├── rag/                            # ingestion + retrieval for the knowledge base
├── agents/
│   ├── state.py                    # FarmProfile, MonitorState (+ SeasonPlan shape)
│   ├── graph_monitor.py             # builds/compiles the monitor graph, run_monitor_sweep()
│   ├── nodes/                        # conversation graph nodes, incl. market_price_lookup.py
│   └── monitor_nodes/                # fetch_weather, compare_thresholds, recompute_*, write_alert
└── scheduler.py                       # APScheduler job sweeping every active farm

scripts/
├── ingest_market_prices.py    # real DAM ingestion — see Market Price Intelligence above
└── ...

tests/                          # pytest — market analytics/decision, financials (plain functions, no DB fixtures needed except where noted)
```

New models go through Alembic: `alembic revision --autogenerate -m "..."` then `alembic upgrade head`.
