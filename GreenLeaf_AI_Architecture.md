# Green Leaf AI — Architecture Reference

Consolidated build spec: system architecture, folder structure, LangGraph pipeline, nodes, and how the whole thing runs end to end. Stack: FastAPI + React (already built), LangChain, LangGraph, pgvector, Postgres, OpenAI API.

---

## 1. System overview

Two LangGraph graphs sit behind the existing FastAPI backend:

- **Conversation graph** — runs once per chat message. Handles intake, weather, RAG, crop/season/financial reasoning, scenario simulation, general Q&A, and chitchat.
- **Monitor graph** — runs independently on a scheduler, one invocation per active farm. Watches the forecast and proactively adjusts plans.

Both graphs share the same Postgres database (with the pgvector extension) for long-term memory and the knowledge base. The FastAPI layer streams every graph event (tokens, tool calls, tool results) to the React dashboard over SSE, which is what powers the live agent-trace panel.

---

## 2. System architecture (layers)

| Layer | Responsibility |
|---|---|
| React frontend | Chat panel + dashboard (farm profile card, live trace log, weather widget, crop comparison, season timeline, financial breakdown, alerts feed, KB sources) |
| FastAPI gateway | REST endpoints (CRUD) + SSE streaming endpoint for live graph events |
| LangGraph orchestrator | Conversation graph + monitor graph |
| LangChain layer | Structured-output parsing, tool wrappers, pgvector retriever, embeddings client |
| Postgres + pgvector | Relational tables (farmer/plan/trace data) + vector column (knowledge base) + LangGraph checkpointer table |
| External APIs | OpenAI API (LLM + embeddings), Open-Meteo (weather + geocoding, keyless) |

---

## 3. Folder structure

```
backend/
  app/
    main.py                          # FastAPI app, mounts routers, starts scheduler on startup
    core/
      config.py                      # env vars: OPENAI_API_KEY, DATABASE_URL, MONITOR_INTERVAL_HOURS
    api/
      routes/
        chat.py                      # POST /chat  (SSE stream of graph events)
        farms.py                     # GET/POST farm profile, dashboard reads
        plans.py                     # GET season plan, financials
        alerts.py                    # GET alerts feed
        trace.py                     # GET historical trace_log for a plan
        monitor.py                   # POST check-weather-now, POST simulate-trigger
      deps.py                        # shared DB session / auth dependency
    agents/
      state.py                       # AgentState, FarmProfile, MonitorState schemas
      graph_conversation.py          # builds + compiles the conversation graph
      graph_monitor.py               # builds + compiles the monitor graph
      router.py                      # supervisor_router (conditional edge logic)
      nodes/
        load_memory.py
        classify_intent.py
        ask_followup.py
        weather_tool.py
        crop_recommendation.py
        season_planner.py
        calculate_financials.py
        general_qa.py
        casual_response.py
        off_topic_redirect.py
        scenario_handler.py
        scenario_blocked.py
        persist.py
      monitor_nodes/
        fetch_weather.py
        compare_thresholds.py
        recompute_season_plan.py
        recompute_financials.py
        write_alert.py
      prompts/
        classify_intent.md
        crop_recommendation.md
        season_planner.md
        general_qa.md
        casual_response.md
    tools/
      weather.py                     # geocode_location, get_weather_forecast (Open-Meteo) + cache/fallback
      rag.py                         # retrieve_agri_knowledge: pgvector search + relevance-grading pass
      financials.py                  # calculate_financials — deterministic function + tool wrapper
    rag/
      ingest.py                      # chunk + embed narrative sources into pgvector
      loaders/
        irri_rkb_loader.py
        soil_atlas_loader.py
        fertilizer_guide_loader.py
      structured_data/
        fertilizer_rates.py          # parses fertilizer tables into Postgres rows (not embedded)
        crop_calendar.py             # parses crop calendar tables into Postgres rows (not embedded)
    db/
      models.py                      # farmers, farms, plans, alerts, trace_log, kb_chunks, fertilizer_rates, crop_calendar
      session.py
      migrations/                    # Alembic
    scheduler.py                     # APScheduler job invoking the monitor graph per active farm
  data/
    raw/                             # downloaded source PDFs (documented in README)
  scripts/
    run_ingestion.py                 # CLI: rebuild the knowledge base
    seed_demo_farm.py                # seed a farm profile for judge-demo reliability
  tests/
    test_financials.py
    test_router.py
    test_compare_thresholds.py
  requirements.txt
  README.md                          # real vs mock table, tools/APIs used, tier reached per feature

frontend/                            # existing React app — new components only
  src/
    components/
      dashboard/
        FarmProfileCard.tsx
        AgentTracePanel.tsx
        WeatherWidget.tsx
        CropComparison.tsx
        SeasonTimeline.tsx
        FinancialBreakdown.tsx
        AlertsFeed.tsx
        KnowledgeSourcesPanel.tsx
      chat/
        ChatWindow.tsx
    hooks/
      useAgentStream.ts               # SSE client, feeds trace panel + chat in real time
```

---

## 4. State schema — Conversation graph (`AgentState`)

| Field | Type | Purpose |
|---|---|---|
| `messages` | list of chat messages | Conversation history (LangGraph message reducer) |
| `farmer_id` | string | Key for memory lookup and checkpointing |
| `intent` | enum: slot_fill / scenario / agro_question / off_topic / chitchat | Set by `classify_intent`, drives routing |
| `farm_profile` | object | location, lat, lon, acres, soil_type, water_availability, budget, season |
| `missing_fields` | list of strings | Which `farm_profile` fields are still unset |
| `weather_data` | object or null | Raw forecast: rainfall, temperature, by day |
| `retrieved_docs` | list of chunks | Each with source_title, content, topic tags — for citations |
| `crop_candidates` | list of objects | crop, suitability, water_need, risk_level, profit_estimate, reasoning |
| `selected_crop` | string or null | Farmer's chosen crop |
| `season_plan` | object or null | sowing_window, fertilizer_schedule, irrigation_schedule, pest_risks, weed_checkpoints, harvest_window |
| `financials` | object or null | cost breakdown, revenue, net_profit, ROI, break_even |
| `scenario_override` | object or null | Derived-only copy of a changed parameter — never mutates the real profile/weather |
| `is_scenario` | boolean | Tells `persist` whether to skip overwriting the committed plan |
| `turn_complete` | boolean | Signals the router to stop looping |
| `trace_log` | list of objects | Every tool call: name, params, raw result, timestamp |

## 5. State schema — Monitor graph (`MonitorState`)

| Field | Type | Purpose |
|---|---|---|
| `farm_id` | string | Which farm this sweep is checking |
| `weather_data` | object | Real or, for the simulate endpoint, injected forecast |
| `weather_override` | object or null | Present only when triggered via the simulate-trigger test endpoint |
| `season_plan` | object | Loaded from Postgres, not from live graph state |
| `triggered` | boolean | Set by `compare_thresholds` |
| `trigger_reason` | string or null | e.g. "runoff risk", "pest window" |
| `updated_plan` | object or null | Recomputed season plan if triggered |
| `updated_financials` | object or null | Recomputed financials if triggered |

---

## 6. Conversation graph — nodes

| Node | Role | Ends the turn |
|---|---|---|
| `load_memory` | Entry point. Loads farm profile, season plan, unread alerts from Postgres | No |
| `classify_intent` | Structured-output classification + opportunistic field/scenario-param extraction | No |
| `ask_followup` | Asks the next targeted question for a missing field (only reached pre-plan) | Yes |
| `weather_tool` | Geocode + real forecast call | No |
| `crop_recommendation` | RAG-grounded ranked crop candidates, ≥3, reasoning built from real values | Yes (waits for selection) |
| `season_planner` | Dated calendar; internally runs targeted RAG for fertilizer, irrigation, and pest/disease sections | No |
| `calculate_financials` | Deterministic cost/yield/ROI/break-even calculation | No |
| `general_qa` | RAG-answered agro question, declines rather than guessing on empty retrieval | Yes |
| `casual_response` | Plain reply for greetings/thanks, no tools | Yes |
| `off_topic_redirect` | Short redirect for non-agricultural questions | Yes |
| `scenario_handler` | Confidence-checks the scenario parameter, re-runs planning/financials against a derived override, returns a delta | Yes |
| `scenario_blocked` | Reached if a scenario question arrives before a plan exists | Yes |
| `persist` | Writes profile/plan/financials/trace to Postgres; skips overwrite if scenario | Yes |

## 7. Conversation graph — routing logic (`supervisor_router`)

Runs after `classify_intent` and again after `weather_tool`. Decision order:

1. If the turn is marked complete → end.
2. If intent is `chitchat` → `casual_response`.
3. If intent is `off_topic` → `off_topic_redirect`.
4. If intent is `agro_question` → `general_qa`.
5. If intent is `scenario` → `scenario_handler` if a season plan already exists, otherwise `scenario_blocked`.
6. Otherwise (intent is `slot_fill`):
   - If a season plan already exists → end (nothing left to ask about).
   - If required fields are still missing → `ask_followup`.
   - If weather hasn't been fetched yet → `weather_tool`.
   - If no crop candidates exist yet → `crop_recommendation`.
   - If a crop has been selected → `season_planner` (which chains automatically into `calculate_financials` → `persist`).

---

## 8. Monitor graph — nodes

| Node | Role |
|---|---|
| `fetch_weather` | Real Open-Meteo call, unless a `weather_override` is present (simulate-trigger path) |
| `compare_thresholds` | Checks both `fertilizer_schedule` and `pest_risks` dates against forecast rainfall/heat; sets `triggered` + `trigger_reason` |
| `recompute_season_plan` | Only runs if triggered — shifts affected milestone dates |
| `recompute_financials` | Only runs if triggered — re-costs the updated plan |
| `write_alert` | Writes an alert row to Postgres and pushes it live to the dashboard over the same SSE channel |

## 9. Monitor graph — trigger and scheduling

- **Scheduler**: APScheduler (`AsyncIOScheduler`), running in-process inside the FastAPI app — no separate broker/service needed.
- **Interval**: every 6 hours in the real background job, configurable via `MONITOR_INTERVAL_HOURS`. Sweeps every active farm, one graph invocation each.
- **Demo path** (separate from the real interval, same graph): two endpoints —
  - `check-weather-now` — real Open-Meteo call, same graph, for genuine on-demand checks.
  - `simulate-trigger` — injects a synthetic forecast via `weather_override`, bypassing only the API call; every downstream node runs the identical real logic. Labeled clearly in the UI as test data, not live.

---

## 10. Tools

| Tool | Purpose | Notes |
|---|---|---|
| `geocode_location` | Farmer's place name → lat/lon | Open-Meteo geocoding, keyless |
| `get_weather_forecast` | Real rainfall/temperature forecast | Cached with short TTL, graceful fallback on API failure — never fabricates a value |
| `retrieve_agri_knowledge` | pgvector similarity search + relevance-grading pass | Query built from structured state, not raw chat text; filtered by crop/topic/region metadata |
| `calculate_financials` | Deterministic cost/yield/revenue/ROI/break-even | Pure function wrapped as a LangChain tool; reused by the plan, the budget slider, and scenario simulation |

---

## 11. RAG design

**Split by data shape, not by source:**

- **Structured/tabular data → Postgres tables, not embeddings.** Fertilizer NPK rate tables and crop calendar sowing/harvest windows are parsed into `fertilizer_rates` and `crop_calendar` tables and queried directly with SQL — precise number lookups don't belong in a similarity search.
- **Narrative/explanatory text → pgvector.** IRRI Rice Knowledge Bank pages and the descriptive sections of the Soil Fertility Atlas get chunked, embedded, and retrieved.

**Ingestion sources**: Fertilizer Recommendation Guide 2018 (BARC), Soil Fertility Atlas Bangladesh 2020 (SRDI), IRRI Rice Knowledge Bank topic pages, FAO/BAMIS crop calendar (structured, not embedded).

**Retrieval pattern**: multiple targeted queries per plan (fertilizer, irrigation, pest/disease, crop suitability) rather than one broad query; each retrieved chunk keeps its source title for citation; a lightweight relevance-grading pass filters out weak matches before they reach the reasoning nodes.

---

## 12. Memory design

- **Short-term / conversational**: LangGraph's Postgres checkpointer, keyed by `farmer_id` as `thread_id` — resumes a session exactly where it left off.
- **Long-term / domain**: dedicated Postgres tables — `farmers`, `farms`, `plans`, `alerts`, `trace_log`, `kb_chunks`, `fertilizer_rates`, `crop_calendar`.
- `load_memory` is what makes cross-session recall real: it hydrates `farm_profile` and `season_plan` from the domain tables before anything else runs each session.

---

## 13. Additional stack pieces

| Piece | Role |
|---|---|
| `langgraph-checkpoint-postgres` | Native graph-state persistence |
| `pgvector` extension | Enabled on the existing Postgres instance — one extension, no new service |
| `text-embedding-3-small` | Embeddings for the knowledge base |
| Alembic | Migrations for the new tables |
| SSE (FastAPI `StreamingResponse` or `sse-starlette`) | Streams graph events to the dashboard's live trace panel |
| APScheduler | Drives the monitor graph sweep |
| Pydantic v2 | Every structured-output schema (intent, crop candidates, season plan, scenario requests) |

---

## 14. Rubric-to-architecture map (quick reference)

| Rubric criterion | Owned by |
|---|---|
| Agentic behavior | `supervisor_router` + full node chain + `trace_log` |
| Accuracy and practicality | `calculate_financials` (deterministic), RAG-grounded reasoning |
| Scope and execution | Conversation graph running end to end, monitor graph as a clean second graph |
| Knowledge base (RAG) | `rag/ingest.py`, `kb_chunks`, `retrieve_agri_knowledge` |
| Explainability | Option-A templated reasoning in `crop_recommendation` and `season_planner` |
| Technical implementation | Clean tool wrapping, structured outputs, Postgres schema |
| Innovation | `scenario_handler`, proactive monitor graph |
