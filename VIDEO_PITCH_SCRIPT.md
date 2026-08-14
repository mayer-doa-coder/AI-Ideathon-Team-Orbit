# Green Leaf AI — 3-Minute Website-Only Video Pitch Script

**Team:** Team Orbit  
**Target runtime:** 2:50–3:00  
**Format:** Presenter voice-over over a screen recording of the Green Leaf AI website only—no slides, presentation file, external B-roll, or separate graphics

**Browser route:** **Home → About → Login → Chat Dashboard → About → Home**

## 0:00–0:10 — Hook

**Website action:** Start at the top of the **Home** page. Keep the Green Leaf AI logo, hero heading, description, and feature checklist visible. Move the cursor toward the main call-to-action as the introduction ends.

**Voice-over:**

> One wrong crop or timing decision can cost a smallholder an entire season. We are Team Orbit, and this is Green Leaf AI.

## 0:10–0:36 — The Problem

**Website action:** Use the website navigation to open **About**. Slowly scroll through **“One farmer, five questions, no single answer”**, pausing on the five questions already displayed on the page.

**Voice-over:**

> Bangladeshi farmers must decide what to grow, when to sow, how much fertilizer to use, what risks to expect, and whether a crop will be profitable. The answers are scattered across weather services and technical references—not combined for one farmer's land, budget, water, and season.

## 0:36–1:00 — The Solution and the Role of AI

**Website action:** Continue down the **About** page to its two-agent explanation and **How It Works** process timeline. Scroll just fast enough to show the conversation-agent steps followed by the monitor-agent loop.

**Voice-over:**

> Green Leaf is an autonomous Bangla and English advisor. Its conversation agent understands natural language, asks for missing details, retrieves Bangladeshi agronomy, and checks live weather. AI uses that evidence to rank crops and build a grounded plan. A second agent monitors it after the chat ends.

## 1:00–2:08 — The Prototype

### 1:00–1:19 — Conversational intake

**Website action:** Use the website header to open **Login**, sign in to the prepared account, and enter the **Chat Dashboard**. Send this prepared message:

> I have 2 acres in Rajshahi with loamy soil, medium irrigation, an 80,000 taka budget, and I am planning for winter.

**Voice-over:**

> Meet a two-acre Rajshahi farmer. One message fills the farm profile; if something is missing, Green Leaf asks one focused question instead of a form.

### 1:19–1:39 — Grounded crop recommendations

**Website action:** Stay on the **Chat Dashboard**. Let the crop cards appear, then scroll the dashboard panel to the live weather widget. Expand one or two agent-trace entries so their tool inputs and results are readable.

**Voice-over:**

> Weather and agronomy are fetched in parallel. The trace shows every tool, input, and result. Green Leaf ranks three or more crops by suitability, water need, risk, reasoning, and estimated profit.

### 1:39–1:56 — Dated and costed plan

**Website action:** Select the leading crop from its card. In the same dashboard, scroll to the generated season timeline and financial breakdown; pause briefly on each.

**Voice-over:**

> After we select a crop, Green Leaf creates a dated journey from sowing through fertilizer, irrigation, pest checks, and harvest. It shows itemized cost, revenue, profit, ROI, and break-even yield. AI builds the grounded plan; reproducible code handles the arithmetic.

### 1:56–2:08 — Proactive monitoring

**Website action:** Log in to or cut to the prepared `demo_farmer` account within the same website. Click **Simulate next check** on the dashboard. Keep the simulated/test labeling visible, then show the adjusted fertilizer date and new alert.

**Voice-over:**

> This labeled test forecast runs the same workflow used with live weather. It detects heavy rain near a fertilizer application, moves the date by four days, updates the plan, and creates an alert. Normally, monitoring runs automatically.

## 2:08–2:34 — The Impact

**Website action:** Remain on the dashboard and scroll upward through the alert, adjusted timeline, financial breakdown, trace, and weather panels. Use the website's language toggle to switch briefly to Bangla, then switch back to English.

**Voice-over:**

> Green Leaf turns fragmented information into plot-specific action. It can help farmers avoid input waste, see risk before spending, and compare agronomic fit with financial outcome. Bangla lowers the information barrier, while sources and tool traces make recommendations inspectable—advice a farmer can understand and trust.

## 2:34–2:52 — The Future

**Website action:** Open **About** from the website navigation and scroll to **“What is built, and what is not.”** Keep that section visible while explaining the roadmap; do not introduce a separate roadmap slide.

**Voice-over:**

> Next, we will pilot with farmers and agricultural officers, measuring accuracy, input savings, and crop outcomes. We can then productionize voice and bdApps access, connect verified suppliers and live market data, add agronomist escalation, and incorporate soil sensors and satellite observations.

## 2:52–3:00 — Closing

**Website action:** Click the Green Leaf AI logo to return to the **Home** page. Hold on the existing hero section and its **“From a Conversation to a Dated Season Plan”** heading until the video ends.

**Voice-over:**

> Green Leaf researches, plans, explains, and keeps watching. One conversation, one living plan, better decisions every season.

---

## Recording Preparation

1. Use only the Green Leaf AI website from the first frame to the last. Browser cuts between existing pages or accounts are fine, but do not insert slides, title cards, stock footage, architecture diagrams, or external graphics.
2. Record the end-to-end intake and crop-selection flow in advance so API loading time can be removed with clean cuts that remain inside the website.
3. Immediately before recording the monitor segment, refresh the reliable demo plan from the `backend` directory:

   ```powershell
   .\venv\Scripts\python.exe -m scripts.seed_demo_farm
   ```

   Use the seeded `demo_farmer` account for the **Simulate next check** shot. This plan deliberately has a pending fertilizer application inside the monitor's look-ahead window.
4. Keep the live agent trace, knowledge sources, weather badge, adjusted timeline date, and alert readable; these are the strongest visual proof that the prototype is agentic and grounded.
5. Capture a backup website recording of every API-dependent section. Edit out waits, but do not edit or relabel outputs in a way that suggests test data is live.
6. Before recording, close unrelated tabs and notifications, hide the bookmarks bar, use a clean browser window, and set zoom so dashboard text remains readable in the final video.
7. Speak at roughly 125–135 words per minute and leave short pauses during page and dashboard transitions.

## Accuracy Guardrails for the Pitch

- Keep the monitor button's simulated/test label visible. The downstream adjustment logic is real, but that button injects a synthetic heavy-rain forecast for a reliable demo.
- Describe the financial figures as transparent reference estimates; the plan calculator currently uses static Bangladesh-oriented cost and yield constants rather than a live price feed.
- Do not claim measured yield gains, farmer adoption, or input savings until a field pilot produces evidence.
- Avoid making voice, a live supplier marketplace, or production payment the center of this video. The planning, grounding, traceability, and monitoring loop is the most complete and defensible prototype story.
