// Mirrors backend/app/schemas/chat.py's serialize_season_plan(), field for
// field, so a monitor-triggered updated_plan/updated_financials (which only
// ever arrive as raw dicts from /api/monitor/*, never pre-serialized) can be
// turned into the same milestones shape SeasonPlanTimeline/MilestoneDetail
// already render, without a round trip through the backend.

function windowText(window) {
  if (!window) return "TBD";
  return `${window.start ?? "TBD"} to ${window.end ?? "TBD"}`;
}

function fertilizerAdjustment(fertilizerSchedule) {
  for (const item of fertilizerSchedule) {
    if (item.adjusted && item.date_before_adjustment) {
      return {
        from: item.date_before_adjustment,
        to: item.date,
        reason: item.adjustment_note || "Adjusted by the monitor agent.",
      };
    }
  }
  return null;
}

export function serializeSeasonPlan(seasonPlan, financials) {
  const itemsByLabel = Object.fromEntries(
    (financials?.items || []).map((item) => [item.label, item.amount])
  );
  const fertilizerSchedule = seasonPlan.fertilizer_schedule || [];
  const pestRisks = seasonPlan.pest_risks || [];
  const irrigationSchedule = seasonPlan.irrigation_schedule || [];
  const weedCheckpoints = seasonPlan.weed_checkpoints || [];

  const fertNames = fertilizerSchedule
    .map((f) => `${f.name} ${f.amount_kg_per_acre}kg/acre (${f.stage}, ${f.date})`)
    .join(", ");
  const pestNames = pestRisks
    .map((p) => `${p.name} (${p.risk_window_start} to ${p.risk_window_end}): ${p.prevention}`)
    .join("; ");
  const irrigationNotes = irrigationSchedule.map((i) => `${i.date}: ${i.note}`).join("; ");
  const weedNotes = weedCheckpoints.map((w) => `${w.date}: ${w.note}`).join("; ");

  const fertilizerMilestone = {
    id: "fertilizer",
    name: "Fertilizer",
    date: fertilizerSchedule.map((f) => f.date).join(", ") || "TBD",
    what: fertNames || "No fertilizer schedule retrieved.",
    why: "Rates and timing grounded in the retrieved fertilizer guidance.",
    quantity: fertNames || null,
    cost: itemsByLabel["Fertilizer"] || 0,
    organicAlternative: null,
  };
  const adjustment = fertilizerAdjustment(fertilizerSchedule);
  if (adjustment) fertilizerMilestone.adjustment = adjustment;

  return [
    {
      id: "sowing",
      name: "Sowing",
      date: windowText(seasonPlan.sowing_window),
      what: `Sow at ${seasonPlan.seed_rate_kg_per_acre ?? "?"} kg/acre seed rate.`,
      why: seasonPlan.reasoning || "",
      quantity: `${seasonPlan.seed_rate_kg_per_acre ?? "?"} kg/acre seed rate`,
      cost: (itemsByLabel["Land Preparation"] || 0) + (itemsByLabel["Seeds"] || 0),
      organicAlternative: null,
    },
    fertilizerMilestone,
    {
      id: "irrigation",
      name: "Irrigation & Weeding",
      date: "Throughout the season",
      what: irrigationNotes || "No irrigation schedule retrieved.",
      why: weedNotes || "",
      quantity: null,
      cost: itemsByLabel["Irrigation"] || 0,
      organicAlternative: null,
    },
    {
      id: "pest",
      name: "Pest & Disease Watch",
      date: "Vegetative stage onward",
      what: pestNames || "No specific pest guidance retrieved.",
      why: "Grounded in the retrieved pest/disease control material for this crop.",
      quantity: null,
      cost: itemsByLabel["Pest & Disease Control"] || 0,
      organicAlternative: null,
    },
    {
      id: "harvest",
      name: "Harvest",
      date: windowText(seasonPlan.harvest_window),
      what: "Harvest when the crop reaches full maturity.",
      why: seasonPlan.reasoning || "",
      quantity: `Expected yield ~${seasonPlan.expected_yield_ton_per_acre ?? "?"} tons/acre`,
      cost: (itemsByLabel["Labor"] || 0) + (itemsByLabel["Post-harvest & Transport"] || 0),
      organicAlternative: null,
    },
  ];
}
