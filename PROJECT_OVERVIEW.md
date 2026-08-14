# AgriSense AI — the whole project, explained simply

This document tells the whole story of AgriSense AI in plain language — the problem it
solves, how it actually works from the moment a farmer types a message to the moment
they get a plan, and what's real versus not-yet-built. No code, no jargon you haven't
already been shown.

For the technical reference (tables, exact tech stack, setup commands), see
[`README.md`](README.md). For a deep, node-by-node walkthrough of the chat agent's
internal logic, see [`CONVERSATION_AGENT_EXPLAINED.md`](CONVERSATION_AGENT_EXPLAINED.md).

---

## 1. The problem

Imagine a farmer — let's call him Rahim — getting ready to plant rice on his 2-acre
plot near Rajshahi. Before he can even buy a seed, he needs answers to a chain of
questions:

- Which variety of rice actually suits his soil and the water he has access to?
- When should he sow, given what the weather looks like this month?
- How much fertilizer, and on which exact days should he apply it?
- What pests should he watch for, and when?
- After buying seed, fertilizer, and paying for labor — will he actually make a
  profit, or lose money?

All of this information *exists* — in weather services, government fertilizer guides,
soil handbooks, and market price boards — but it's scattered across different sources,
written for agronomists, not farmers, and nobody hands Rahim one clear, dated plan
built specifically around *his* two acres.

AgriSense AI is built to be the thing that does that: a farmer describes their farm in
a normal conversation, and the system does the research and the arithmetic for them.

---

## 2. The two-agent idea

Most chatbots are one thing: you ask, it answers. AgriSense AI is built as **two
separate "agents"** (two independent decision-making systems) that share the same
database:

- **The conversation agent** — this is the one Rahim actually talks to. It runs once
  every time he sends a message. It asks what it still needs to know, looks things up
  for real (weather, farming references, market prices), and builds his plan.
- **The monitor agent** — this one Rahim never directly talks to. Once his plan
  exists, it wakes up on a schedule (like a background job checking in periodically)
  and asks: *"has the real weather forecast changed in a way that would hurt this
  plan?"* If a big rain is now forecast right when Rahim's plan says to apply
  fertilizer (which would just wash it away and waste money), the monitor agent
  pushes the fertilizer date back on its own and tells Rahim why — without him having
  to ask, or even be online.

Both agents read and write to the same database, so whichever one makes a change, the
other sees it immediately. If the monitor agent quietly adjusts Rahim's plan overnight,
the next time he opens the chat, it already reflects that change.

---

## 3. Walking through a real conversation

Here's what actually happens, step by step, the first time Rahim uses it.

**Step 1 — He describes his farm.**
He might type something like *"I have 2 acres near Rajshahi, clay soil, I have
irrigation, budget is 30,000 taka, planning for the Boro season."* The system reads
this and pulls out each fact (location, size, soil type, water, budget, season). If
anything's missing, it asks one focused follow-up question at a time — never a long
form to fill out.

**Step 2 — It checks the real weather.**
Once it knows Rahim's location, it calls a live weather API (Open-Meteo) to get an
actual forecast for his area — rainfall and temperature for the coming days. This
isn't guessed or remembered from training data; it's a real API call, made right then,
and it's shown in the app's "trace" panel so you can see the actual request and
response.

**Step 3 — It suggests crops.**
Using Rahim's soil, water, season, and the real forecast, it asks an AI model to
suggest at least three suitable crop options, each with a suitability rating, water
need, risk level, and a profit estimate — and, when real market-price data is
available for that crop, a note on whether prices are currently good to sell into.
Every suggestion has to point back to something real: retrieved reference material or
the actual weather, never an unexplained guess.

**Step 4 — It looks things up before it plans.**
Before writing the season plan, the system searches a knowledge base built from real
Bangladeshi agricultural references — a BARC handbook, a fertilizer recommendation
guide, a soil atlas — to find the specific fertilizer rates, irrigation timing, and
pest risks that apply to Rahim's chosen crop. (See section 6 for exactly how that
search works.) If the knowledge base doesn't have a good enough match, it does a real
web search instead of making something up.

**Step 5 — It builds a dated plan.**
With that grounded information plus the real forecast, it produces an actual
calendar: a sowing window, specific fertilizer application dates with exact
quantities, an irrigation schedule, pest-risk windows with prevention notes, and a
harvest window.

**Step 6 — It works out the money.**
Using fixed, transparent cost figures (seed price, fertilizer price, labor, etc.) it
calculates total cost, expected revenue, profit, return on investment, and the
break-even yield — a plain calculation, not an AI guess, so the same inputs always
produce the same numbers.

**Step 7 — Every step is shown, not hidden.**
Every real lookup the system makes — the weather call, the knowledge-base search, the
market-price check — gets logged to a visible "trace" panel in the app in real time.
You can literally watch, as it happens, which tool was called, what was sent to it,
and what came back. Nothing is a black box.

---

## 4. What happens after the plan exists

This is where the **monitor agent** takes over. On a set schedule, it re-checks the
real weather forecast for every farm that has a committed plan and asks two
deterministic (rule-based, not AI-guessed) questions:

- Is heavy rain forecast right around a day fertilizer is supposed to go down? If so,
  push that application back a few days rather than let rain wash the fertilizer away.
- Is a pest's risk window opening soon, with rain conditions that make an outbreak more
  likely? If so, flag it as active and surface the prevention guidance.

If either is true, it recalculates the financial impact of the change and writes an
alert — all without Rahim asking, and all visible the next time he opens the app.

---

## 5. The disease doctor

If Rahim notices spots on his crop's leaves, he can send a photo instead of typing.
Two independent checks run on it:

1. A real plant-disease identification service (Kindwise's crop.health) analyzes the
   photo and returns its top three guesses with confidence scores and treatment
   suggestions.
2. Separately, an AI vision model looks at the *same* photo and gives its own opinion,
   without being told which answer is "expected."

The system only calls a diagnosis "high confidence" when **both** independently agree.
If they disagree, it says so honestly and asks a clarifying question instead of
picking one arbitrarily. If either check fails outright, nothing is invented to fill
the gap — the farmer is told the check failed, plainly.

---

## 6. How it finds facts it doesn't already "know" (in plain terms)

An AI language model doesn't actually know current fertilizer doses or this week's
weather — it has to look them up, the same way a person would search a reference book
instead of guessing. Here's the simple version of how that lookup works:

1. Ahead of time, real reference documents (government handbooks, guides) were broken
   into small, topic-coherent passages — not just chopped every few hundred
   characters, but split at the document's own section headings, so each passage
   stays about one clear thing (e.g., "fertilizer application for rice").
2. Each passage was converted into a list of numbers (an "embedding") that captures
   its meaning, using an OpenAI model, and stored in the database alongside the text.
3. When the agent needs an answer, it turns the question into that same kind of number
   list and asks the database: "which stored passages are numerically closest in
   meaning to this?" That's the actual search — comparing meaning, not just matching
   exact words.
4. It only trusts a match that's actually close enough. If the best match is still
   pretty distant (meaning nothing in the reference material is truly relevant), the
   system doesn't force an answer from a weak match — it falls back to a real web
   search instead.

Structured numeric data (like fixed fertilizer-rate tables) is kept in plain database
tables instead of going through this "search by meaning" process, since exact lookups
are more reliable for numbers than similarity search is.

---

## 7. Bengali language support (and what's not done yet)

The whole chat interface, dashboard, and site can be switched between English and
Bengali with a single toggle in the top-right corner of the chat page. Every button,
label, heading, and status message was translated by hand (not machine-translated on
the fly), so the Bengali reads naturally rather than like a direct word-for-word
conversion.

**Voice input/output was attempted but is currently turned off.** The plan was: record
a voice message, transcribe it to text (via OpenAI's Whisper), let the same agent
answer it exactly like a typed message, then speak the reply back in Bengali using a
text-to-speech model. The backend pieces for this still exist in the codebase, but the
feature isn't reliable enough yet, so the microphone button in the app is currently
disabled rather than shipped half-working.

---

## 8. What's real, and what's a placeholder today

Being upfront about this matters more than looking finished. As of now:

**Actually working, end-to-end, with real external calls:**
- The core conversation flow: intake, real weather, crop suggestions, dated season
  plans, financial calculations, and the visible trace log.
- The knowledge-base search (RAG) described in section 6, grounded in real ingested
  documents.
- The monitor agent's proactive plan adjustments.
- Plant disease detection from an uploaded photo.
- Bengali-language UI.

**Not currently functional (placeholder only):**
- Marketplace and supplier comparison.
- Market price intelligence card (sell/store/wait verdict).
- BDApps payment gateway integration.
- Voice input/output (built, but disabled — see section 7).

This list can drift as the project keeps changing — [`README.md`](README.md)'s
"Feature coverage by tier" table is the up-to-date source of truth; if the two ever
disagree, trust the README.

---

## 9. How it's actually built (in plain terms)

- **The two agents** (conversation and monitor) are built with **LangGraph**, a
  framework for wiring together a sequence of steps ("nodes") where each step can
  decide what happens next — rather than one giant AI prompt trying to do everything
  at once. Splitting it into small, named steps (intake, weather lookup, crop ranking,
  planning, ...) is what makes the trace log possible: each step reports exactly what
  it did.
- **The backend** (the server that runs the agents) is written in Python using
  **FastAPI**.
- **The database** is **PostgreSQL**, with an extra piece called **pgvector** that lets
  it do the "search by meaning" lookups described in section 6.
- **The frontend** (what you see in the browser) is built with **React**.
- **The AI model calls** go to **OpenAI's API** — one model for conversation and
  reasoning, and a separate call for looking at uploaded photos.

---

## 10. Where to go next

- Want the exact tech stack, API list, and setup instructions? → [`README.md`](README.md)
- Want to understand exactly what each step of the conversation agent does,
  node by node? → [`CONVERSATION_AGENT_EXPLAINED.md`](CONVERSATION_AGENT_EXPLAINED.md)
- Want to see the actual compiled agent graph as a picture? →
  [`conversation_agent_graph.png`](conversation_agent_graph.png)
- Want the full walkthrough of the SMS/USSD/payment integration? →
  [`BDAPPS_INTEGRATION.md`](BDAPPS_INTEGRATION.md)
- Want the plain-language breakdown of persistent memory, proactive alerts,
  the fertilizer/pest scheduling, and "what if" scenarios? →
  [`TIER_1_FEATURES.md`](TIER_1_FEATURES.md)
