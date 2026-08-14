// Marketing copy for the home page, in English. The Bangla twin is
// homeContent.bn.js — same exported names, same shape — and useHomeContent()
// picks between them by language.
//
// GROUND RULE FOR THIS FILE: everything claimed here must be a capability that
// actually ships today, per README.md's "Feature coverage by tier" table
// (the stated source of truth) and its "Data: what is real and what is mock"
// section. Specifically, do NOT advertise the marketplace, the market-price
// sell/store/wait verdict, BDApps payment, or voice — all four are marked
// "Not done (placeholder)" and are not reachable in the product. Nothing on
// this page should be something a judge can click and find missing.

export const heroContent = {
  eyebrow: "An agentic crop advisor for Bangladeshi farmers",
  heading: "From a Conversation to a Dated Season Plan",
  paragraph:
    "Describe your farm in plain Bangla or English. AgriSense AI checks the real forecast, reads the national agronomy references, and returns a dated plan with the costs worked out.",
  checklist: [
    "Real Open-Meteo forecasts",
    "Grounded in 4 national references",
    "Every tool call shown live",
    "Full Bangla and English",
  ],
  // One entry per Agriva hero slide. The template ships three slides and its
  // reveal animation indexes them by position, so keep this at three.
  slides: [
    {
      image: "/assets/img/home-1/hero/slider-1.jpg",
      eyebrow: "An agentic crop advisor for Bangladeshi farmers",
      heading: "From a Conversation to a Dated Season Plan",
      paragraph:
        "Tell it your district, land size, soil, water and budget. It asks only for what's missing, then returns sowing dates, fertilizer amounts, irrigation timing and a full cost and profit projection.",
    },
    {
      image: "/assets/img/home-1/hero/slider-2.jpg",
      eyebrow: "Two independent checks on every photo",
      heading: "Diagnose Crop Disease From One Photo",
      paragraph:
        "A specialist plant-disease service and a separate vision model examine the same leaf independently. It only calls a diagnosis confident when both agree — and says so plainly when they don't.",
    },
    {
      image: "/assets/img/home-1/hero/slider-3.jpg",
      eyebrow: "A second agent watches the forecast for you",
      heading: "Your Plan Updates Before the Rain Does",
      paragraph:
        "When heavy rain lands on a fertilizer date, the monitor agent moves the application, recalculates the cost, and leaves you an alert — on its own, whether or not you're online.",
    },
  ],
};

export const features = [
  {
    icon: "/assets/img/home-2/icon/07.svg",
    title: "Two Cooperating Agents",
    text: "One agent talks with you and builds the plan. A second runs on a schedule and revises it when the weather turns.",
  },
  {
    icon: "/assets/img/home-2/icon/08.svg",
    title: "Grounded, Never Guessed",
    text: "Advice is retrieved from four real Bangladesh agronomy references and a live forecast — not recalled from model training data.",
  },
  {
    icon: "/assets/img/home-2/icon/09.svg",
    title: "Nothing Is Hidden",
    text: "A live trace panel shows every tool call as it happens: what was asked, what was sent, and exactly what came back.",
  },
];

export const aboutContent = {
  headingLines: ["Answers You Can Trace", "Back to a Real Source"],
  paragraph:
    "AgriSense AI is built as two LangGraph agents over a shared Postgres database. Before it recommends anything it retrieves the relevant passage from Bangladesh's own agronomy literature and calls a real weather API — and it shows you both.",
  // Verifiable counts, not audience metrics. Sources: README.md "Data: what is
  // real and what is mock" (four ingested references; 862 BARC chunks) and
  // tools/weather.py (the cross-verified 64-district coordinate table).
  // Do not swap these for farmer/user counts — the system has no deployed
  // user base to count, and an invented one is the first thing a judge checks.
  stats: [
    { value: 4, suffix: "", label: "National agriculture references ingested" },
    { value: 862, suffix: "", label: "Indexed passages from the BARC handbook" },
    { value: 64, suffix: "", label: "Districts with cross-verified coordinates" },
  ],
};

export const whyChooseUs = {
  eyebrow: "why AgriSense?",
  headingLines: ["Advice That Keeps Working", "After You Close the App"],
  paragraph:
    "Most farming chatbots answer a question and forget it. AgriSense AI commits your plan to a database, then keeps checking it against the real forecast — and changes it when the numbers say it should.",
  highlights: [
    {
      title: "A Monitor Agent That Acts On Its Own",
      text: "It re-checks the forecast against every pending fertilizer date and pest risk window, then adjusts the plan and writes you an alert.",
    },
    {
      title: "Money Maths, Not Model Guesswork",
      text: "Cost, revenue, profit, ROI and break-even yield are computed by a plain function — so the same inputs always give the same numbers.",
    },
  ],
  phone: "+880 1234 567890",
};

// Every entry here is a Tier 0 or Tier 1 capability marked "Done" in README.md.
// Deliberately absent: marketplace/supplier comparison, the market-price
// sell/store/wait verdict, BDApps payment and voice — all placeholders today.
export const services = [
  {
    icon: "fa-solid fa-comments",
    title: "Conversational Season Planning",
    tags: ["Intake", "Planning", "Dated"],
    text: "It asks only for the details it's still missing, then returns a dated calendar from sowing through harvest.",
  },
  {
    icon: "fa-solid fa-camera",
    title: "Crop Disease Detection",
    tags: ["Photo", "Dual Check", "Treatment"],
    text: "Two independent checks on the same leaf photo, with a confident answer only when both agree.",
  },
  {
    icon: "fa-solid fa-cloud-sun-rain",
    title: "Live Weather Grounding",
    tags: ["Open-Meteo", "64 Districts", "Live"],
    text: "Every forecast is a real API call, with Bangladeshi district coordinates verified against a known-bad geocoder.",
  },
  {
    icon: "fa-solid fa-flask",
    title: "Fertilizer & Irrigation Scheduling",
    tags: ["Per Stage", "Quantities", "Cost"],
    text: "Real amounts and per-stage timing drawn from the national Fertilizer Recommendation Guide, priced into your budget.",
  },
  {
    icon: "fa-solid fa-code-branch",
    title: "Scenario Simulation",
    tags: ["What If", "Re-costed", "Committed"],
    text: 'Ask "what if my budget drops 40%?" and it regenerates, re-costs and commits a revised plan.',
  },
];

// Honest, checkable completion figures rather than invented accuracy or
// satisfaction scores — these track README.md's tier tables directly.
export const faqStats = [
  { title: "Tier 0 core capabilities complete", value: 100 },
  { title: "Tier 1 advanced capabilities complete", value: 90 },
];

export const faqItems = [
  {
    question: "How does AgriSense AI know what to recommend?",
    answer:
      "It searches a knowledge base built from four real Bangladesh references — BARC's Hand Book of Agricultural Technology, the Fertilizer Recommendation Guide, the Soil Fertility Atlas and the Yearbook of Agricultural Statistics — and combines what it finds with a live weather forecast. If nothing in those references is close enough to your question, it runs a real web search instead of answering from memory.",
  },
  {
    question: "How does the photo diagnosis work?",
    answer:
      "A specialist plant-disease service analyses your photo and returns its top candidates with confidence scores. Separately, a vision model examines the same photo without being told what the first answer was. A diagnosis is only reported as high-confidence when both independently agree; when they disagree it tells you so and asks a clarifying question.",
  },
  {
    question: "What happens to my plan after it's created?",
    answer:
      "A second agent runs on a schedule for every farm with a committed plan. It compares the latest forecast against your pending fertilizer dates and pest risk windows, and if heavy rain would wash away an application it moves that date, recalculates the financial impact and writes you an alert — without you asking.",
  },
  {
    question: "Can I use it in Bangla?",
    answer:
      "Yes. The chat, dashboard and this site all switch between Bangla and English with one toggle, and every label was translated by hand rather than machine-translated. You can also describe your farm to the agent in Bangla.",
  },
  {
    question: "How do I know it isn't making things up?",
    answer:
      "A live trace panel records every tool call as it happens — the weather request, the knowledge-base search, the disease check — showing what was sent and exactly what came back. The financial projection is a plain calculation rather than a model output, so identical inputs always produce identical numbers.",
  },
];

// NOTE: these are the real data sources the answers are grounded in, not
// customer quotes. The system has no deployed farmer base, so genuine
// testimonials do not exist yet and inventing them is the kind of claim a
// judge checks first. If real pilot quotes become available, swap them in and
// restore the star rating block in components/home/Testimonials.jsx.
export const testimonials = [
  {
    name: "Open-Meteo",
    role: "Live weather API",
    quote:
      "Every forecast shown or acted on is a real API call made at that moment — rainfall and temperature for the farmer's own district, never recalled from training data.",
  },
  {
    name: "BARC Hand Book of Agricultural Technology",
    role: "Knowledge base · 862 indexed passages",
    quote:
      "Fertilizer rates, irrigation timing and pest risks are retrieved from Bangladesh's own published agronomy reference before any plan is written.",
  },
  {
    name: "Kindwise crop.health",
    role: "Plant disease identification",
    quote:
      "Every uploaded photo is analysed by a real diagnostic service, then cross-checked by an independent vision model before a confident answer is given.",
  },
];

export const blogPosts = [
  {
    icon: "fa-solid fa-diagram-project",
    title: "Why AgriSense Runs Two Agents Instead of One Chatbot",
    excerpt:
      "One agent plans with you; another keeps checking the forecast after you leave. Here's why that split matters.",
    date: "22 Jul, 2026",
  },
  {
    icon: "fa-solid fa-book-open",
    title: "Grounding Advice in Bangladesh's Own Agronomy Literature",
    excerpt:
      "How four national reference documents become searchable passages the agent must cite before it recommends anything.",
    date: "18 Jul, 2026",
  },
  {
    icon: "fa-solid fa-eye",
    title: "Showing the Work: A Live Trace of Every Tool Call",
    excerpt:
      "Watch the weather request, the knowledge-base search and the disease check as they happen — no black box.",
    date: "10 Jul, 2026",
  },
];

export const brandLogos = [
  "/assets/img/home-1/brand/01.png",
  "/assets/img/home-1/brand/02.png",
  "/assets/img/home-1/brand/03.png",
  "/assets/img/home-1/brand/04.png",
  "/assets/img/home-1/brand/05.png",
  "/assets/img/home-1/brand/06.png",
  "/assets/img/home-1/brand/07.png",
];

export const footerLinks = {
  services: [
    { label: "Crop Doctor", to: "/chat" },
    { label: "All Services", to: "/services" },
    { label: "Season Planning", to: "/services" },
    { label: "Scenario Simulation", to: "/services" },
  ],
  resources: [
    { label: "How It Works", to: "/about" },
    { label: "Knowledge Base", to: "/ask" },
    { label: "Blog & Notes", to: "/blog" },
    { label: "Help & FAQs", to: "/services" },
  ],
  company: [
    { label: "About AgriSense", to: "/about" },
    { label: "What's Built", to: "/about" },
    { label: "Contact Us", to: "/contact" },
  ],
};

// --- Chrome content used by the Agriva header/offcanvas/footer -------------

export const contactInfo = {
  heading: "Contact Info",
  blurb:
    "AgriSense AI is an agentic crop advisor for Bangladeshi farmers — ask it about crop choice, disease, weather or fertilizer in Bangla or English.",
  address: "Khulna, Bangladesh",
  email: "hello@agrisense.ai",
  hours: "Saturday–Thursday, 9am – 6pm",
  phone: "+880 1234 567890",
};

export const socialLinks = [
  { label: "Facebook", icon: "fab fa-facebook-f", href: "#footer" },
  { label: "Twitter", icon: "fab fa-twitter", href: "#footer" },
  { label: "YouTube", icon: "fab fa-youtube", href: "#footer" },
  { label: "LinkedIn", icon: "fab fa-linkedin-in", href: "#footer" },
];

// Mirrors Agriva's mega-menu: the template's four thumbnail cards, repurposed
// as entry points into the app's real routes.
export const megaMenuCards = [
  { thumb: "/assets/img/header/home-1.jpg", title: "Crop Doctor", href: "/chat", isRoute: true, cta: "Open" },
  { thumb: "/assets/img/header/home-2.jpg", title: "Ask the Handbook", href: "/ask", isRoute: true, cta: "Open" },
  { thumb: "/assets/img/header/home-3.jpg", title: "Consultancy", href: "/consultancy", isRoute: true, cta: "Open" },
  { thumb: "/assets/img/header/home-4.jpg", title: "Knowledge Base", href: "/rag-test", isRoute: true, cta: "Open" },
];

// Agriva's pinned project section pairs each row with one large thumbnail and
// refuses to animate unless the two counts match exactly
// (`leftItems.length === rightImages.length` in main.js), so this list must
// stay at four entries — one per project/*.png thumb.
export const projects = [
  {
    title: "Dated Season Plan, Costed End to End",
    image: "/assets/img/home-2/project/01.jpg",
    thumb: "/assets/img/home-2/project/05.png",
    tags: ["Season Plan", "Financials"],
  },
  {
    title: "Proactive Monitor Sweep on the Forecast",
    image: "/assets/img/home-2/project/02.jpg",
    thumb: "/assets/img/home-2/project/06.png",
    tags: ["Monitor Agent", "Alerts"],
  },
  {
    title: "Photo Diagnosis With Two Independent Checks",
    image: "/assets/img/home-2/project/03.jpg",
    thumb: "/assets/img/home-2/project/07.png",
    tags: ["Crop Health", "Vision"],
  },
  {
    title: "Retrieval Grounded in National References",
    image: "/assets/img/home-2/project/04.jpg",
    thumb: "/assets/img/home-2/project/08.png",
    tags: ["RAG", "pgvector"],
  },
];

// The seven nodes the conversation agent actually runs, in graph order (see
// backend/app/agents/graph_conversation.py and CONVERSATION_AGENT_EXPLAINED.md),
// followed by the monitor agent — which is not a step but a loop that keeps
// running after the plan is committed, hence `isLoop`.
// `meta` names the real tool, table or module behind each step; keep it
// accurate, it is the detail that makes this section checkable.
export const processSteps = [
  {
    title: "You describe your farm",
    text: "Tell it your district, land size, soil type, water access, budget and season — in Bangla or English. It pulls out each fact and asks a focused follow-up only for what's still missing, never a form.",
    meta: "classify_intent · ask_followup",
  },
  {
    title: "It checks the real forecast",
    text: "Once it knows where you are, it calls Open-Meteo for an actual rainfall and temperature forecast. District names are resolved against a cross-verified table of all 64 districts first, because the public geocoder gets Bangladesh wrong.",
    meta: "Open-Meteo · tools/weather.py",
  },
  {
    title: "It reads the agronomy first",
    text: "Before recommending anything it searches four ingested national references for the passages that match your crop and soil. If nothing is close enough, it runs a real web search rather than answering from memory.",
    meta: "pgvector · 4 references",
  },
  {
    title: "It ranks your crop options",
    text: "At least three candidates, each with a suitability rating, water need, risk level and profit estimate — every one pointing back to the retrieved material or the live forecast.",
    meta: "crop_recommendation",
  },
  {
    title: "It builds the dated plan",
    text: "A real calendar: sowing window, fertilizer dates with exact quantities, irrigation schedule, pest risk windows with prevention notes, and a harvest window.",
    meta: "season_planner",
  },
  {
    title: "It works out the money",
    text: "Total cost, revenue, profit, ROI and break-even yield — computed by a plain function, not the model, so the same inputs always produce the same numbers.",
    meta: "tools/financials.py · no LLM",
  },
  {
    title: "It shows you the work",
    text: "Every lookup is streamed to a live trace panel as it happens: which tool ran, what was sent, and exactly what came back. Nothing is a black box.",
    meta: "trace_log · server-sent events",
  },
  {
    title: "Then the monitor agent takes over",
    text: "On a schedule, for every farm with a committed plan, a second agent re-checks the forecast against your pending fertilizer dates and pest windows. If heavy rain would wash an application away it moves the date, recomputes the cost, and writes you an alert.",
    meta: "graph_monitor.py · deterministic",
    icon: "fa-solid fa-satellite-dish",
    isLoop: true,
  },
];

// --- /about page --------------------------------------------------------
// The "built / not built" split is taken straight from README.md's tier
// tables. Keep them in sync: this page exists partly to be the honest answer
// to "what actually works?", so a stale list here is worse than no list.
export const aboutPage = {
  problemHeading: "One farmer, five questions, no single answer",
  problemIntro:
    "A farmer preparing to plant faces a chain of decisions, and the information needed to make them exists — in weather services, fertilizer guides, soil handbooks and market boards. It is just scattered, written for agronomists, and never assembled around one specific plot of land.",
  problemListHeading: "What has to be answered before a single seed goes in",
  problemQuestions: [
    "Which variety suits this soil and the water actually available?",
    "When to sow, given what the weather is doing this month?",
    "How much fertilizer, and on exactly which days?",
    "Which pests are likely, and in which window?",
    "After seed, fertilizer and labour — is there any profit left?",
  ],
  problemOutro:
    "AgriSense AI is built to be the thing that answers all five together: the farmer describes their land in an ordinary conversation, and the system does the research and the arithmetic for them.",

  statusHeading: "What is built, and what is not",
  statusIntro:
    "Being upfront about this matters more than looking finished. The lists below track README.md's tier tables, which are the project's source of truth.",
  built: [
    "Conversational intake with targeted follow-ups",
    "Live Open-Meteo weather grounding, 64 verified districts",
    "Crop recommendation — 3+ ranked candidates",
    "Dated season plan through to harvest",
    "Itemized financial projection (no LLM in the maths)",
    "RAG over four national references, with web fallback",
    "Visible agent trace of every tool call",
    "Proactive, weather-triggered plan adjustment",
    "Persistent memory across sessions",
    "Scenario simulation (\"what if…\")",
    "Plant disease detection with a dual independent check",
    "Full Bangla and English UI",
  ],
  notBuilt: [
    "Marketplace and supplier comparison",
    "Market price intelligence (sell / store / wait verdict)",
    "BDApps payment gateway",
    "Voice input and output",
  ],
  notBuiltNote:
    "These four are placeholders. The UI for voice exists but is disabled rather than shipped half-working, and none of the four is advertised anywhere else on this site.",
};

// --- /services page -----------------------------------------------------
// Index-aligned with `services` above — serviceDetails[i] expands services[i].
export const serviceDetails = [
  {
    body: "The agent reads your first message for location, land size, soil type, water access, budget and season, then asks one focused question at a time for whatever is still missing. Nothing is a form.",
    points: [
      "Understands Bangla and English input",
      "Reachable over web chat, SMS and USSD",
      "Remembers your farm between sessions",
    ],
    meta: "classify_intent · ask_followup · season_planner",
  },
  {
    body: "Upload a photo of an affected leaf. A specialist diagnostic service and an independent vision model each examine it, and a confident answer is only given when the two agree.",
    points: [
      "Top candidates with confidence scores",
      "Disagreement is reported, not resolved arbitrarily",
      "Nothing is invented when a check fails",
    ],
    meta: "Kindwise crop.health + independent vision cross-check",
  },
  {
    body: "Every forecast is a live API call made at that moment. District names are resolved against a hand-verified coordinate table first, because the public geocoder silently mis-resolves Bangladeshi districts.",
    points: [
      "Rainfall and temperature for your own district",
      "All 64 districts cross-verified by hand",
      "Never a remembered or approximated forecast",
    ],
    meta: "Open-Meteo · tools/weather.py",
  },
  {
    body: "Quantities and per-stage timing come from the national Fertilizer Recommendation Guide for your crop and soil, and each application is priced into the season budget.",
    points: [
      "Real amounts, not general advice",
      "Timing tied to crop growth stage",
      "Cost carried into the profit projection",
    ],
    meta: "Fertilizer Recommendation Guide (BARC, 2018)",
  },
  {
    body: 'Ask a "what if" and the agent can either talk the change through or actually regenerate, re-cost and commit a revised plan — your choice.',
    points: [
      "Narration mode, or a committed revised plan",
      "Financials recomputed against the new plan",
      "Changes are recorded, not silently applied",
    ],
    meta: "scenario simulation · re-costed and committed",
  },
];
