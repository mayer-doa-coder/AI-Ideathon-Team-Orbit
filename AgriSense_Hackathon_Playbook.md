# AgriSense AI — Hackathon Playbook
### bdapps Agentic AI Hackathon (powered by Codex) · IUT 12th ICT Fest · Final Round

---

## 0. Reality check first — read this before anything else

Your event clock, from the problem statement:

| Milestone | Time |
|---|---|
| Check-in & briefing | 24 July, 08:00 |
| **Hacking starts** | **24 July, 09:00** |
| Hacking ends | 25 July, 09:00 |
| Demo & judging | 25 July, 10:00 |

Today **is** 24 July. That means there is no multi-week runway to take full courses before you touch code — if you're reading this before check-in, you have at most an hour or two. So this playbook is built around one idea: **you learn by building, inside the 24 hours, in the exact order you'll need each concept.** Nobody on a winning team at an event like this "already knew agentic AI" going in — they learned five specific ideas just-in-time and leaned on Claude to fill gaps live.

If you're reading this *before* 09:00 — do only Phase 0 (below), then stop and go to check-in.
If you're already inside the 24 hours — skip to whichever Phase matches your elapsed time.

---

## 1. The headline answers to your questions

**What should we learn?** Only five ideas, nothing more, in this order:
1. Agent vs. chatbot (the loop: gather info → call a tool → observe → decide → repeat)
2. Tool/function calling (how an LLM asks your code to run something and gets a real answer back)
3. RAG — retrieval before generation (look up real documents, then let the model write using them)
4. State/memory (carrying farm details across turns and sessions)
5. Explainability/tracing (logging every tool call so a judge can verify it wasn't invented)

Everything else — vector databases, agent frameworks, multi-agent orchestration — is optional polish, not a requirement to win.

**Should you use LangChain/LangGraph?** Given one of you already has a basic handle on it: **yes, use LangGraph as your orchestration layer.** The usual objection to it tonight would be the ramp-up — independent 2026 comparisons peg LangGraph's learning curve at roughly 1–2 weeks for someone starting from zero<cite index="10-1">LangGraph is the production leader for complex, stateful workflows... but a 1–2 week learning curve</cite> — but that overhead doesn't apply to your team, since it's not being learned from scratch. That removes the main reason to avoid it, and LangGraph actually buys you real things the rubric rewards: its typed state schema *is* your FarmProfile, each step of the agent (ask a follow-up, call weather, retrieve knowledge, rank crops, calculate financials) is naturally one node, and its conditional edges are exactly the "ask a targeted follow-up only for missing fields" logic Tier 0 asks for. Its built-in checkpointer also gets you most of the way to Tier 1's persistent-memory requirement without hand-rolling storage yourself.

Have the teammate who already knows LangGraph own the graph structure (state schema, nodes, edges, checkpointer) from Phase 1 onward, and pair with the other two early so they can read it independently by the middle of the day — Appendix B has "explain this to me" prompts specifically for when graph code (nodes/edges/routing) is unclear to whoever didn't write it.

**Is this problem already solved somewhere?** The general *category* — an LLM agent that gathers farm info, pulls live weather, recommends crops, and grounds advice in retrieved documents — has several public reference projects: AWS's sample "farm-management-ai-agent," a research system called AgroAskAI that does exactly this weather→RAG→advice pipeline, and various crop-recommendation repos on GitHub<cite index="14-1">one AWS sample solution integrates real-time weather data, web search for agricultural best practices, and memory-enabled conversations to track farm conditions over time</cite><cite index="18-1">a published multi-agent system called AgroAskAI sources data through retrieval-augmented generation from sources like NASA's climate data and OpenWeather forecasts, orchestrated by a central agent manager</cite>. Skim one of these for architectural ideas (linked in Appendix A) — but the exact spec you were given (this tier structure, this bdapps integration) isn't sitting anywhere as a repo to copy, and the rules explicitly forbid bringing pre-built project code in anyway. Use them to sanity-check your design, never to copy code from.

**Where are the free resources + videos?** See Appendix A — ranked by how many minutes you actually have.

**How do we not burn Claude's limits?** See Section 3 below — this is the single highest-leverage thing you can do differently from most teams tonight.

---

## 2. Recommended architecture (keep it this boring)

```
┌─────────────────────────┐      ┌──────────────────────────────┐
│   Frontend (simple)      │      │  Agent Service (new, Python)  │
│  React or plain HTML/JS  │◄────►│  FastAPI + LangGraph           │
│  - chat UI                │      │  - StateGraph (nodes+edges)    │
│  - "agent trace" panel    │      │  - tool: get_weather()         │
└─────────────────────────┘      │  - tool: search_knowledge_base()│
                                    │  - tool: calc_financials()     │
                                    │  - crop ranking logic           │
                                    └───────────┬────────────────────┘
                                                │ calls when user reaches
                                                │ checkout / OTP / subscribe
                                                ▼
                                    ┌──────────────────────────────┐
                                    │  Existing PHP bdapps service   │
                                    │  (you already have this!)      │
                                    │  send_otp / verify_otp /       │
                                    │  check_subscription / ussd /   │
                                    │  sms / unsubscribe             │
                                    └──────────────────────────────┘
```

Why this shape:
- Your PHP bdapps files (`send_otp.php`, `verify_otp.php`, `check_subscription.php`, `subscription_listener.php`, `unsubscribe.php`, `ussd.php`, `sms.php`, `sdk_file.php`) already work and already talk to `developer.bdapps.com`. **Do not rewrite them tonight.** Treat them as a finished service you wire into your UI in Phase 7.
- The actual agent (weather, RAG, crop logic, planning) is far easier to build fast in Python — every free course and library you'll lean on tonight (Appendix A) is Python-first.
- The agent service is a LangGraph `StateGraph`: state = FarmProfile + weather + retrieved chunks + trace log; nodes = intake, weather, retrieval, crop-ranking, planning, financials; edges = conditional routing (e.g. missing field → back to intake node).
- One clean seam between the two means a bug in one never blocks the other, which matters a lot when you're tired at 3 AM.

Weather API: use **Open-Meteo**. No signup, no API key, no rate-limit wait — you can call it in the first ten minutes<cite index="40-1">Open-Meteo requires no API key, no sign-up, and no credit card, with non-commercial use up to 10,000 daily API calls free</cite>. That single fact removes the biggest early-hours time-sink (waiting on an API key approval email).

**Database: PostgreSQL.** Since you're committing to Postgres, the fastest path tonight is a **free hosted instance** (Neon or Supabase both spin one up in about 2 minutes and hand you a connection string — no local server install, no Docker). Grab that connection string as literally your first task once the clock starts, since everything downstream depends on it. LangGraph has an equally first-class Postgres checkpointer package, `langgraph-checkpoint-postgres`, with `PostgresSaver` (sync) and `AsyncPostgresSaver` (async) — install with `pip install -U "psycopg[binary,pool]" langgraph langgraph-checkpoint-postgres`, import `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio`<cite index="70-1">langgraph-checkpoint-postgres installs psycopg (Psycopg 3), and when using Postgres checkpointers for the first time you must call .setup() to create the required tables</cite>. Since you're on FastAPI (async), use the async variant and call `.setup()` once on startup. Practical upshot: build your plain `messages` table in the same Postgres database in Step 1a below, and when you add LangGraph in Step 1b, its checkpointer writes its own tables into that same database — one connection string for the whole app.

---

## 3. Claude Pro usage-limit strategy for a team of 3

Anthropic doesn't publish a fixed "N messages/day" number — usage is session-based (resets roughly every 5 hours) plus a weekly cap, and it scales with message length, attachments, conversation length, tool use, and which model/effort level you pick<cite index="50-1">usage is a "conversation budget" affected by conversation length, features used, model, and effort level, with different plans having different allowances</cite><cite index="47-1">Pro plans have a session-based limit that resets roughly every five hours, plus a separate weekly cap across all models</cite>. Practically, for tonight:

1. **You have 3 Pro accounts — use all 3 in parallel**, not one person driving. Split by lane: the teammate who knows LangGraph basics owns the graph/agent logic (state schema, nodes, edges, checkpointer), a second person owns frontend + trace panel, the third owns RAG knowledge base + bdapps wiring. Three separate quotas instead of one account doing everything.
2. **Set up ONE Claude Project per lane** and upload the problem PDF, the bdapps API PDF, and the relevant existing PHP files into **Project Knowledge** once. Content stored in Project Knowledge is cached and doesn't re-count against your limit every time it's referenced<cite index="46-1">content in projects is cached and doesn't count against your limits when reused, and similar prompts you use frequently are partially cached</cite>. Don't paste these files into chat over and over.
3. **Default to Sonnet 5** for almost everything tonight (fast, cheap on your limit). Reserve **Opus 4.8** only for: gnarly multi-file bugs, the financial-math logic (get this right once, carefully), and architecture decisions you're unsure about.
4. **Start a fresh chat per task/phase**, not one giant 6-hour thread. Long conversations resend their whole history with every message, which eats your limit faster and also degrades quality.
5. Don't ask Claude to re-search the web repeatedly for things this playbook already gives you (Appendix A). Every extra tool call costs more of your session.
6. If someone's account runs dry, rotate to a teammate's, or — if you have a card on file — Pro plans let you enable pay-as-you-go usage credits to keep going past the included limit<cite index="48-1">usage credits allow individuals subscribed to paid Claude plans to continue working after reaching their plan's usage limits by switching to consumption-based pricing at standard API rates</cite>.

---

## Phase 0 — Crash primer (do this once, ~45 min, before or right at check-in)

**Goal:** get the mental model straight, on paper, before anyone opens an editor.

**Concept, in plain words:** A chatbot answers the message in front of it. An agent runs a loop: *figure out what's missing → decide which tool to call → call it → look at the real result → decide the next step → repeat until done.* Tonight's whole job is building that loop around five tools: weather, knowledge-base search, crop ranking, financial calculator, and a trace logger.

**Prompt 1 — paste into a new Claude chat (Sonnet 5):**
```
I'm a total beginner about to start a 24-hour agentic AI hackathon. Explain, in plain
beginner language with a concrete example using MY exact problem below, what makes
something an "agent" instead of a chatbot. Use the farmer/crop-planning example
throughout. Keep it under 400 words. Then list, as a numbered list, the 5 technical
concepts I need to understand tonight (nothing more) to build it — one sentence
per concept, no jargon.

[paste the "What agentic means for this challenge" section from the problem PDF]
```

**Prompt 2 — same chat:**
```
Sketch the minimum-viable architecture for this, assuming: Python FastAPI backend,
a free hosted PostgreSQL instance (e.g. Neon or Supabase) for storage, and
OpenAI's API directly at first — planning to prove that plain plumbing works end
to end before introducing LangGraph as the orchestration layer on top (one
teammate already knows LangGraph basics). Weather via Open-Meteo (no API key
needed), and an existing PHP service (already built) for OTP/subscription/payment
that I'll wire in near the end. Give me a file/folder structure I can create in
the first 10 minutes, nothing fancy — including where the StateGraph, state
schema, and node functions will live once we add LangGraph.
```

Do **not** start coding yet. Go to check-in. Come back for Phase 1 once the clock starts.

---

## Phase 1 (Hour 0–2): Setup & scaffolding — plumbing first, then wrap in LangGraph

**Goal:** two checkpoints in this phase, not one. First prove the boring plumbing works end to end (frontend → FastAPI → OpenAI → PostgreSQL → back). Only then introduce LangGraph on top of it. This order matters: if something breaks after Step 1b, you know the bug is in the LangGraph layer, not in three unknowns stacked at once — and if 1b overruns, you still have a working (if unstructured) app rather than a half-wired graph.

**Step 1a — bare plumbing (~30–45 min):**
```
First, spin up a free hosted PostgreSQL instance (Neon or Supabase — a couple of
minutes) and grab the connection string. Then create a minimal FastAPI project
with:
- a POST /chat endpoint that takes {thread_id, message}, calls the OpenAI API
  directly (chat completions, no agent framework yet) with a system prompt
  describing a farm-advisor's job, and returns the reply as JSON
- a PostgreSQL connection (SQLAlchemy or asyncpg, your call) with one table:
  messages(thread_id, role, content, timestamp). Every call should store the
  new message and load prior history for that thread_id before calling OpenAI.
No agent logic yet, no LangGraph yet — I want to prove the round trip (frontend
-> backend -> OpenAI -> Postgres -> back to frontend) actually works before we
add anything else. Explain each piece as you build it.
```
Confirm it for real: send a message from the frontend, see a genuine OpenAI reply, see the row land in Postgres (check via your host's dashboard or `psql`), restart the server and see history reload. That's your proof the plumbing is solid.

**Step 1b — wrap it in LangGraph (rest of Hour 0–2):**
```
Now introduce LangGraph as the orchestration layer on top of what we just
proved works — don't throw the plumbing away, restructure around it:
- state.py: a State (TypedDict) holding farm profile fields, weather data,
  retrieved chunks, trace log, and messages
- graph.py: a StateGraph with an intake node (wraps the OpenAI call from
  Step 1a) and a stub weather node, wired with conditional edges that route
  back to intake while required fields are missing, otherwise forward
- swap our hand-written messages table for LangGraph's AsyncPostgresSaver
  checkpointer (from langgraph.checkpoint.postgres.aio, needs
  langgraph-checkpoint-postgres and psycopg[binary,pool] — remember to call
  .setup() once on startup to create its tables), pointed at the same Postgres
  connection string, so thread-based persistence now comes from LangGraph itself
- a tools/ folder with weather_tool.py calling Open-Meteo
  (https://api.open-meteo.com/v1/forecast, no API key needed)
Keep the actual OpenAI-calling logic mostly intact — move it inside the intake
node rather than rewriting it. Explain each new file in plain English, as if
some of the team has never seen a state graph before.
```

**Prompt (after Claude scaffolds it):**
```
Walk me through graph.py line by line as if I'm seeing LangGraph for the first
time. Specifically: what does the State TypedDict actually hold, how does a node
read/update it, how does a conditional edge decide where to go next, and where
would I add a second node (e.g. for RAG retrieval) later?
```

**Watch-out:** don't skip straight to 1b. The 30–45 minutes on bare plumbing isn't wasted — it's the cheapest way to find out your OpenAI key works, your DB writes correctly, and your frontend can reach your backend, before a new framework's abstractions are also in the mix.

---

## Phase 2 (Hour 2–6): Conversational intake + live weather grounding
*(Tier 0, capabilities 1 & 2)*

**Concept:** the agent must collect location, farm size, soil type, water availability, budget, and target season — asking only about what's actually missing, not a fixed script. Then it must call Open-Meteo with the farm's real coordinates and use the actual numbers, never invented ones.

**Prompt 1:**
```
Flesh out the intake node so State tracks a FarmProfile (location, farm_size,
soil_type, water_availability, budget, target_season). Given a vague opening
message like "I want to plant something on my 2 acre land", the node should
identify which fields are still missing and the conditional edge should route
back to intake asking ONE targeted follow-up question at a time — not a wall of
questions — until every field is filled, then move on to the weather node. Show
me the updated State schema, the intake node function, and the routing function
for the conditional edge.
```

**Prompt 2:**
```
Now flesh out the weather node: once location is known, geocode it (Open-Meteo
has a free geocoding endpoint at https://geocoding-api.open-meteo.com/v1/search —
no key), call the forecast tool, and write the result into State. In every
response after this node runs, the agent must literally quote the real returned
rainfall/temperature numbers, and must never generate a forecast on its own. Add
an assertion/test that fails loudly if a response mentions weather without a
matching entry in State's trace log — this is a hard requirement for the demo.
```

**Model:** Sonnet 5 is fine for both.

---

## Phase 3 (Hour 6–10): Knowledge base + RAG + crop recommendation
*(Tier 0, capabilities 3 & 7 — worth 12 pts alone for the knowledge base)*

**Concept:** RAG just means "look up real documents before answering" instead of trusting the model's memory. You don't need a hosted vector database tonight — a folder of text files + a simple similarity search is completely legitimate and is what judges are checking for (that retrieval genuinely feeds the advice), not the sophistication of the storage layer.

**Prompt 1:**
```
I need to build a small RAG knowledge base for Bangladesh crop advisory, tonight,
with no budget for a hosted vector DB. Recommend: (a) 4-6 specific, publicly
available, real sources for crop calendars, fertilizer guides, and soil/yield data
for Bangladesh (e.g. BRRI, DAE, BARI publications) that I can legally scrape or
download text from in the next 20 minutes, and (b) the simplest possible working
RAG setup in Python — chunking, a free embedding approach, and a plain
cosine-similarity search — that a beginner can get running in under an hour.
Do not invent fake source names — only recommend ones you're confident actually
exist and are public.
```

**Prompt 2:**
```
Add a retrieval node and a crop-ranking node to the graph. The retrieval node
should search the knowledge base and write matching chunks into State. The
ranking node should read State (farm profile, weather, retrieved chunks) and
return at least 3 candidate crops, each with suitability score, water need, risk
level, and a rough profit estimate — every field must cite which retrieved chunk
or weather value it came from. Show the data structure so the frontend can
render a comparison table later, and where these two nodes sit in the graph's
edges relative to intake/weather.
```

**Watch-out — anti-hallucination check (run this once now, and again in Phase 8):**
```
Read through rank_crops and the RAG retrieval code. Flag anything where a number
in the output (suitability score, profit estimate, yield, price) is NOT directly
traceable to either (a) a retrieved knowledge-base chunk, (b) the weather tool
result, or (c) explicit user input. I want a list of every place the model might
currently be "filling in" a plausible-sounding number instead of computing or
retrieving it.
```

---

## Phase 4 (Hour 10–14): Season plan + financial projection
*(Tier 0, capabilities 4 & 5)*

**Concept:** for the chosen crop, produce a dated calendar (sowing → fertilizer → irrigation → pest checks → harvest) and an itemized cost/revenue/profit/ROI/break-even calculation that's internally consistent — change an input, outputs change correctly.

**Prompt 1:**
```
Add a season-plan node to the graph: generate_season_plan(crop, sowing_date,
growth_stages) outputs a dated calendar of actions from land prep to harvest,
each tied to a growth stage and a rough date. Base the stage lengths and timing
on the retrieved knowledge-base chunks already sitting in State from Phase 3,
not on general model knowledge — show me where each date comes from and how
this node reads State.
```

**Prompt 2:**
```
Add a financials node: calculate_financials(crop, farm_size, cost_inputs,
expected_yield, market_price) returning itemized costs, expected revenue, net
profit, ROI %, and break-even point, written into State. Write 4-5 unit tests
that change one input at a time (e.g. double the farm size) and assert the
outputs change in the mathematically correct direction. I need to be able to
show a judge this math is real, not model vibes.
```

**Model:** consider Opus 4.8 for this prompt specifically — financial math correctness is worth checking with your strongest reasoning model once.

---

## Phase 5 (Hour 14–16): Explainability + visible agent trace
*(Tier 0, capabilities 6 & 8 — completes Tier 0)*

**Concept:** every recommendation must name the specific inputs behind it, and the UI must expose a log of every tool call, its parameters, and its raw return value, so a judge can verify a number came from a real call.

**Prompt 1:**
```
Add a trace_log list to State that every node appends to when it calls a tool:
node name, parameters sent, raw response, timestamp. Expose it via a GET /trace
endpoint (feel free to also show me how LangGraph's own state history for a
thread could double as a source for this, if that's simpler than hand-tracking
it). Then build a simple collapsible panel in the frontend that renders this
trace live next to the chat, so a judge can click and see "get_weather(lat, lon)
-> {rainfall: 42mm, ...}" for example.
```

**Prompt 2:**
```
Rewrite the final recommendation text generation so every sentence that states a
number or fact explicitly references its source inline, e.g. "Apply 45kg/acre
urea in the next 3 days, because your soil is sandy (you told us), rice is at
vegetative stage (day 25 of your season plan), and no rain is forecast this week
(Open-Meteo, 0mm over next 7 days)." Show me 2 example outputs.
```

At this point, **Tier 0 is complete.** Stop and run a full end-to-end demo of it before touching anything else — this is your fallback if nothing else gets finished.

---

## Phase 6 (Hour 16–19): Pick 2 Tier 1 features, no more

**Concept:** Tier 1 is where strong teams differentiate, but scope control matters more than feature count — pick two you can finish cleanly rather than four half-built ones. Best picks for time-to-value:
- **Persistent memory** (remembers the farm across sessions, not just one chat) — highest judge weight, and mostly already done, since Phase 1b already wired the AsyncPostgresSaver checkpointer.
- **Scenario simulation** ("what if rainfall drops 30%?") — cheap to build if Phase 4's financial function already takes clean inputs; just re-run it with modified inputs.

**Prompt 1 (memory):**
```
We already have LangGraph's AsyncPostgresSaver checkpointer wired in from
Phase 1b, so state should already be surviving across turns. Verify (and fix if
needed) that it also survives across sessions: when a returning farmer sends a
message on a thread_id we've seen before, the graph should resume from their
saved FarmProfile and conversation state instead of starting the intake node
over. Show me how the frontend passes/stores thread_id between visits, and add
a quick test: end a session, restart the frontend, send a follow-up message on
the same thread_id, and confirm the farmer isn't asked to repeat themselves.
```

**Prompt 2 (scenario simulation):**
```
Add a handle_scenario_query(original_plan, modification) function that detects
when the user asks a "what if" question (e.g. rainfall drops X%, budget cut Y%),
re-runs calculate_financials and the season plan with the modified input, and
returns a clearly diffed comparison (old vs new numbers), not a generic answer.
```

**If time remains after these two:** fertilizer/irrigation scheduler or pest/disease risk are the next-best picks — same prompt pattern (ground it in Phase 3's knowledge base, never invent numbers).

---

## Phase 7 (Hour 19–21): Wire in bdapps — OTP, subscription (2tk/day), payment

**Concept:** you already have working PHP endpoints for this. Tonight's job is integration, not learning a new payment system from scratch.

**Prompt 1:**
```
Here are my existing working PHP files for bdapps OTP and subscription (they
already call developer.bdapps.com and work): [paste or reference send_otp.php,
verify_otp.php, check_subscription.php, unsubscribe.php from Project Knowledge]

I want to add a simple subscription gate in my frontend: before showing full
season-plan results, the user must verify their phone via OTP (calling
send_otp.php / verify_otp.php) and be subscribed to the daily 2tk service
(check_subscription.php). Show me the minimal frontend flow (3 screens: enter
number -> enter OTP -> subscribed/checkout) and the fetch calls to these
existing endpoints. Do not modify the PHP logic itself unless something is
actually broken — just tell me if you spot a bug before we wire it in.
```

**Prompt 2 (payment/CaaS simulation, Tier 2):**
```
Referencing the bdapps API documentation in Project Knowledge, help me build a
sandbox/simulator-mode checkout flow that showcases request/response for the
CaaS charging flow, operator balance deduction, and a receipt — clearly labeled
in the UI and README as "simulated" wherever we don't have live sandbox
credentials. Never fabricate what a real response would look like without
flagging it as illustrative.
```

**Watch-out:** the rules require your README to state clearly what's real vs. mock in this exact flow — don't let this slide to the last five minutes.

---

## Phase 8 (Hour 21–23): Testing, hallucination audit, README, demo script

**Prompt 1 — full hallucination audit (do this for real, not skip it):**
```
Act as a skeptical judge. Go through the entire app's output for one full sample
conversation and flag every single number, date, or fact that is NOT clearly
traceable to: (1) a tool call in the trace log, (2) a knowledge-base retrieval,
or (3) explicit user input. For each flagged item, tell me exactly where in the
code it's being generated instead of retrieved/computed, and suggest the
minimal fix.
```

**Prompt 2 — README:**
```
Write a README.md covering: setup instructions, tools/APIs used (real vs mock,
explicitly labeled), which tier each feature reaches, and known limitations.
Use this exact submission requirement text as your checklist: [paste "Submission
Requirements" section from the problem PDF]. Keep it scannable — judges skim.
```

**Prompt 3 — demo script (try Fable 5 here for a more compelling narrative voice):**
```
I have 4 minutes to demo this live, then 2-3 minutes of Q&A. Write a tight demo
script: what I show first (the hook), the order of features to click through to
hit all 5 "agentic behavior" criteria (tool use, multi-step planning, missing-
info handling, memory, explainability), and 3 likely judge questions with sharp
honest answers — including "what's mocked vs real" since they explicitly said
they'll notice if that's fudged.
```

---

## Phase 9 (Hour 23–24): Final commit & submission

- Repo name: `TeamName_AgriSense` (per the rules).
- Final commit must be pushed **before** the hard cutoff — commits after don't count.
- Do one last read of the "What Not to Do" section of the problem PDF as a team, out loud, before you submit.
- Sleep/shift tip: with 3 people over 24 hours, stagger 2-hour rest blocks starting around hour 14–16 rather than everyone crashing at once near the end — you want at least one alert person during Phase 8's audit.

---

## Appendix A — Free learning resources, ranked by minutes available

**If you have 10 minutes:** Hugging Face's "Introduction to Agents" page — the single best plain-English explanation of the think→act→observe loop<cite index="33-1">the unit covers how LLMs serve as the brain behind an agent, how agents use external tools, and the Think → Act → Observe cycle</cite>. `https://huggingface.co/learn/agents-course/en/unit1/introduction`

**If you have 1–2 hours (do this during any lull, e.g. while waiting on a teammate):**
- DeepLearning.AI, "Agentic AI" (Andrew Ng) — short course, free, no card required: `https://learn.deeplearning.ai/courses/agentic-ai`
- DeepLearning.AI, "AI Agents in LangGraph" — worth following along this time since you're actually building on LangGraph tonight: `https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/`
- LangGraph official quickstart (nodes, edges, state, checkpointers) — best as a quick reference to dip into mid-build rather than read start to finish: `https://langchain-ai.github.io/langgraph/`

**If you have a free evening after the hackathon (to actually get good at this):**
- Hugging Face full AI Agents Course — free certificate, ~8 hours across 4 units, hands-on<cite index="32-1">to get a certificate of completion you need to complete Unit 1, one use-case assignment, and the final challenge</cite>. `https://huggingface.co/learn/agents-course`

**Reference architectures to skim for ideas (not to copy code from):**
- AWS sample farm-management agent: `https://github.com/aws-solutions-library-samples/gudiance-for-farm-management-ai-agent-on-aws`
- AgroAskAI paper (weather + RAG + agent-manager pattern): `https://arxiv.org/html/2512.14910`

**Tools:**
- Open-Meteo (weather, no key): `https://open-meteo.com/`
- Your bdapps API doc PDF and existing PHP files are already in this project — use them as-is in Phase 7.

---

## Appendix B — Recurring prompts for when vibe-coded code gets confusing

Use these anytime, in any phase, whenever a teammate is staring at code nobody wrote by hand:

```
Explain what this specific function does, in plain English, as if I've never
seen this pattern before. Don't rewrite it — just explain it. Then tell me what
would break if I deleted it.
```

```
I don't understand why [X] is happening. Don't just fix it — first explain what
you think is causing it and how you'd verify that theory, then fix it.
```

```
Add a one-line comment above every function in this file explaining what it does
and why it exists, so someone who didn't write it can follow it under pressure.
```

---

## Appendix C — Judging rubric self-check (run this in the last hour)

```
Here is the judging rubric: [paste the "Judging Criteria" table from the problem
PDF]. Given everything we've built [paste your README], score us honestly against
each of the 8 criteria out of the listed points, and tell me the single highest-
leverage thing we could still fix in the time remaining to raise our weakest
score.
```
