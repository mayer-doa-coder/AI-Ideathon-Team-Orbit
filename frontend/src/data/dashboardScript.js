// Field metadata for the Farm Profile strip only. The actual onboarding
// flow is freeform, LLM-driven slot filling (backend's ask_followup node) —
// the farmer can volunteer several fields in one message — so this no
// longer drives a fixed question/option wizard, just icons/labels for
// whatever fields the agent has filled in so far.
export const onboardingSteps = [
  { field: "location", label: "Location" },
  { field: "acreage", label: "Land" },
  { field: "soilType", label: "Soil" },
  { field: "water", label: "Water" },
  { field: "budget", label: "Budget" },
  { field: "season", label: "Season" },
];

export const greeting =
  "Hi, I'm your Green Leaf AI planning assistant. Tell me about your farm — location, " +
  "acreage, soil type, water availability, budget, and the season you're planning for — " +
  "and I'll check the weather and knowledge base to build you a season plan.";
