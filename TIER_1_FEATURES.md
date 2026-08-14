# Tier 1 features, explained simply

"Tier 1" is one of the hackathon's own difficulty levels for this problem statement —
Tier 0 is the required core (a working conversation that produces a plan), Tier 1 is
the "Advanced" tier on top of that, and Tier 2 is "Ambitious" bonus work. This document
explains, in plain language, what the five Tier 1 capabilities actually are and how
each one really works in this project.

For the exact up-to-date status of every feature (including these), see the "Feature
coverage by tier" table in [`README.md`](README.md) — treat that as the source of
truth if anything here ever seems out of date. For the whole-project walkthrough, see
[`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md).

The five Tier 1 capabilities are:

1. Persistent memory across sessions
2. Proactive, weather-triggered plan adjustment
3. A fertilizer and irrigation scheduler tied to the crop and soil, with real cost
4. Pest and disease risk prediction
5. Scenario simulation ("what if...")

---

## 1. Persistent memory across sessions

**In plain words:** if a farmer closes the app and comes back tomorrow — or logs in
from a different phone — everything they already told the system, and the plan it
built for them, is still there. Nothing has to be re-entered, and nothing is
forgotten.

This actually relies on two separate kinds of memory working together:

- **The farm's permanent facts** (location, soil type, water, budget, season, the crop
  they picked, the season plan, the financial numbers) live in real database tables.
  Every time a new chat message comes in, the system re-reads these tables first —
  which is also what makes it possible for the background monitoring feature
  (capability 2, below) to update a farmer's plan even while they're not using the app
  at all, and have that change be there the next time they open it.
- **The conversation itself** (the back-and-forth message history, what's already been
  asked and answered) is kept by a separate piece called a "checkpointer," which saves
  the conversation's state to the same database, keyed to that farmer's account. This
  is what lets the farmer pick up mid-conversation instead of starting over.

Both of these survive a logout/login, a server restart, or switching devices, because
neither one lives only in the browser or only in memory — they're both written to a
real, durable database.

---

## 2. Proactive, weather-triggered plan adjustment

**In plain words:** the system doesn't just make a plan once and stop paying
attention. It keeps checking the real weather forecast in the background, and if
something's about to go wrong, it fixes the plan *before* the farmer would have found
out the hard way — without them having to ask.

This is done by a second, independent process (referred to elsewhere as "the monitor
agent") that wakes up on a schedule and checks every farm that has a committed plan
against two specific, rule-based conditions — not an AI guess, a real calculation:

- **Fertilizer runoff risk:** if a fertilizer application is due soon (within the next
  5 days) and at least 30mm of rain is forecast right around that date, applying it on
  schedule would mostly just get washed away and wasted. When this is detected, the
  system pushes that one fertilizer application back by 4 days on its own.
- **Pest/disease risk:** if a tracked pest or disease's risk window is opening soon
  (within 5 days) and at least 25mm of rain is forecast in the next few days, that's
  exactly the humid, waterlogged condition that lets diseases like bacterial leaf
  blight spread fastest in rice. When this is detected, the system marks that risk as
  actively "watching" and surfaces the prevention guidance.

Only one of these gets acted on per check (whichever is found first) — that keeps each
alert focused on one clear change instead of dumping several warnings on the farmer at
once; anything else gets caught on the next scheduled check. Either way, the plan's
cost numbers get recalculated to match the change, and an alert is written explaining
exactly what changed and why — all visible the next time the farmer opens the app.

---

## 3. Fertilizer and irrigation scheduler, tied to crop and soil, with cost

**In plain words:** the season plan isn't just "use fertilizer at some point" — it's
an actual dated calendar: which fertilizer, how much per acre, and on which specific
day, plus an irrigation schedule, built specifically around the crop and soil the
farmer described, and grounded in retrieved agricultural reference material rather
than guessed.

Each fertilizer entry carries a name, the growth stage it applies to, an exact date,
and a quantity in kilograms per acre — and that quantity feeds directly into the real
cost calculation (capability 3 also directly powers the financial breakdown described
in the main project walkthrough). The irrigation schedule works the same way: specific
dated notes rather than a vague "water regularly."

**One honest gap:** the data has a field reserved for an "organic alternative" to each
fertilizer recommendation, but the model doesn't currently fill it in — it's always
empty today, not hidden, just not yet generated.

---

## 4. Pest and disease risk prediction
 
**In plain words:** alongside the fertilizer/irrigation calendar, the season plan also
lists which pests or diseases are a real risk for that crop, in which growth-stage
window, with a prevention note for each — grounded the same way the fertilizer advice
is, in retrieved reference material plus the real forecast.

This is also the piece that connects directly to capability 2 above: if the real
weather later matches the risky conditions a predicted pest/disease needs to spread,
the monitor agent is what actually escalates that specific risk from "watching" to
"active."

**Two honest gaps**, which is why the README calls this one "mostly done" rather than
fully done:
- The cost of dealing with pests/diseases is captured as one combined "Pest & Disease
  Control" line in the overall budget, not a separate itemized cost per individual
  predicted risk.
- There's a single `prevention` text field reused both for "how to prevent this" and
  "what to do if it's already happening" — rather than two clearly separate pieces of
  guidance.

---

## 5. Scenario simulation ("what if...")

**In plain words:** a farmer can ask a hypothetical question — *"what if my budget
drops 40%?"* or *"what if I only had 1 acre instead of 2?"* — and get a real, grounded
answer, either just as an explanation, or as an actual update to their saved plan, if
they ask for that.

There are genuinely two different modes here, and the system tells them apart by what
the farmer actually asked for:

- **Just asking ("what if...?")** — the system works out the answer and explains it in
  the reply, but never touches the farmer's actual saved plan. Pure "what would happen
  if," nothing committed.
- **Actually asking to apply it ("update the plan," "apply that")** — this time the
  system regenerates a real, revised plan (using the exact same grounded plan-building
  process as the original one), lets the model decide which real levers make sense to
  pull (less fertilizer, a smaller area, a cheaper input) rather than following one
  fixed hardcoded strategy, prices the result with the same real, deterministic
  financial calculator used everywhere else, and actually saves it.

**One deliberate refusal, not a bug:** if someone asks to *apply* a hypothetical
weather change (e.g. "apply what happens if it doesn't rain this month"), the system
won't do it. There's only one real weather forecast for a location — it's not a
rain simulator — so faking an alternate forecast just to regenerate a plan against it
would break the project's core rule of never inventing a number. Real,
forecast-driven changes are what capability 2 (the monitor agent) is for instead.

---

## Where this lives in the code, if you want to look

| Capability | Main files |
|---|---|
| Persistent memory | `backend/app/agents/nodes/load_memory.py`, `backend/app/agents/checkpointer.py` |
| Weather-triggered adjustment (monitor agent) | `backend/app/agents/graph_monitor.py`, `backend/app/agents/monitor_nodes/*.py` |
| Fertilizer/irrigation scheduler | `backend/app/agents/nodes/season_planner.py` |
| Pest/disease risk prediction | `backend/app/agents/nodes/season_planner.py`, `backend/app/agents/monitor_nodes/compare_thresholds.py` |
| Scenario simulation | `backend/app/agents/nodes/scenario_handler.py` |
