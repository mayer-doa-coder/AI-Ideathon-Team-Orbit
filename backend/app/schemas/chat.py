from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Browser-reported current position for this message (e.g. from
    # navigator.geolocation), opt-in on the frontend. Distinct from the
    # farm's own registered farm_profile.lat/lon — a farmer asking "urea
    # near my area" from town isn't asking about their farm's location.
    lat: float | None = None
    lon: float | None = None
    # Base64-encoded photo (no data: URI prefix) attached to this message.
    # When present, the turn is routed straight to disease_detection instead
    # of the normal intake path — see router.intake_router.
    image_base64: str | None = None
    # Base64-encoded voice message (no data: URI prefix) attached to this
    # message. When present, the turn is routed straight to voice_input
    # instead of the normal intake path — see router.intake_router.
    audio_base64: str | None = None
    # The farmer's current UI language ("bn" or "en"), sent by the frontend's
    # language toggle. Used only as the speech-to-text language hint for
    # audio_base64 — see tools/voice.transcribe_audio, where it measurably
    # improves Bangla accuracy over auto-detection. Not used to translate
    # anything; the agent already replies in the language it is addressed in.
    language: str | None = None


def serialize_crop_candidates(candidates: list[dict]) -> list[dict]:
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "suitability": c["suitability"],
            "water": c["water_need"],
            "risk": c["risk_level"],
            "profit": c["profit_estimate"],
            "why": {"knowledge": c["reasoning_knowledge"], "weather": c["reasoning_weather"]},
            "market": c.get("market"),
        }
        for c in candidates
    ]


def _short_date(iso_date: str) -> str:
    try:
        from datetime import date

        y, m, d = (int(x) for x in iso_date.split("-"))
        return date(y, m, d).strftime("%b %-d")
    except Exception:
        return iso_date


def serialize_weather(weather_data: dict, location: str) -> dict:
    dates = [_short_date(d) for d in weather_data.get("dates", [])]
    rainfall = weather_data.get("daily_rainfall_mm", [])
    temp_min = weather_data.get("daily_temp_min_c", [])
    temp_max = weather_data.get("daily_temp_max_c", [])

    heavy_rain_index = next((i for i, mm in enumerate(rainfall) if mm >= 20), None)
    heavy_rain_date = dates[heavy_rain_index] if heavy_rain_index is not None else None

    return {
        "location": location,
        "dates": dates,
        "daily_rainfall_mm": rainfall,
        "temp_range_c": f"{min(temp_min) if temp_min else '?'}–{max(temp_max) if temp_max else '?'}",
        "heavy_rain_date": heavy_rain_date,
        "alert": (
            f"Heavy rain (~{rainfall[heavy_rain_index]:.0f}mm) forecast around {heavy_rain_date} — "
            f"consider timing fertilizer and irrigation around it."
            if heavy_rain_index is not None
            else None
        ),
    }


def _window_text(window: dict | None) -> str:
    if not window:
        return "TBD"
    return f"{window.get('start', 'TBD')} to {window.get('end', 'TBD')}"


def _fertilizer_adjustment(fertilizer_schedule: list[dict]) -> dict | None:
    """Surfaces the monitor graph's most recent adjustment (if any) into the
    shape SeasonPlanTimeline/MilestoneDetail already render (`{from, to,
    reason}`) — this is what makes a monitor-triggered plan change visible
    in the season timeline, not just in the alerts feed."""
    for item in fertilizer_schedule:
        if item.get("adjusted") and item.get("date_before_adjustment"):
            return {
                "from": item["date_before_adjustment"],
                "to": item["date"],
                "reason": item.get("adjustment_note") or "Adjusted by the monitor agent.",
            }
    return None


def serialize_season_plan(season_plan: dict, financials: dict | None) -> list[dict]:
    items_by_label = {item["label"]: item["amount"] for item in (financials or {}).get("items", [])}
    fertilizer_schedule = season_plan.get("fertilizer_schedule", [])
    pest_risks = season_plan.get("pest_risks", [])
    irrigation_schedule = season_plan.get("irrigation_schedule", [])
    weed_checkpoints = season_plan.get("weed_checkpoints", [])

    fert_names = ", ".join(
        f"{f['name']} {f['amount_kg_per_acre']}kg/acre ({f['stage']}, {f['date']})"
        for f in fertilizer_schedule
    )
    pest_names = "; ".join(
        f"{p['name']} ({p['risk_window_start']} to {p['risk_window_end']}): {p['prevention']}"
        for p in pest_risks
    )
    irrigation_notes = "; ".join(f"{i['date']}: {i['note']}" for i in irrigation_schedule)
    weed_notes = "; ".join(f"{w['date']}: {w['note']}" for w in weed_checkpoints)

    fertilizer_milestone = {
        "id": "fertilizer",
        "name": "Fertilizer",
        "date": ", ".join(f["date"] for f in fertilizer_schedule) or "TBD",
        "what": fert_names or "No fertilizer schedule retrieved.",
        "why": "Rates and timing grounded in the retrieved fertilizer guidance.",
        "quantity": fert_names or None,
        "cost": items_by_label.get("Fertilizer", 0),
        "organicAlternative": None,
    }
    adjustment = _fertilizer_adjustment(fertilizer_schedule)
    if adjustment:
        fertilizer_milestone["adjustment"] = adjustment

    return [
        {
            "id": "sowing",
            "name": "Sowing",
            "date": _window_text(season_plan.get("sowing_window")),
            "what": f"Sow at {season_plan.get('seed_rate_kg_per_acre', '?')} kg/acre seed rate.",
            "why": season_plan.get("reasoning", ""),
            "quantity": f"{season_plan.get('seed_rate_kg_per_acre', '?')} kg/acre seed rate",
            "cost": items_by_label.get("Land Preparation", 0) + items_by_label.get("Seeds", 0),
            "organicAlternative": None,
        },
        fertilizer_milestone,
        {
            "id": "irrigation",
            "name": "Irrigation & Weeding",
            "date": "Throughout the season",
            "what": irrigation_notes or "No irrigation schedule retrieved.",
            "why": weed_notes or "",
            "quantity": None,
            "cost": items_by_label.get("Irrigation", 0),
            "organicAlternative": None,
        },
        {
            "id": "pest",
            "name": "Pest & Disease Watch",
            "date": "Vegetative stage onward",
            "what": pest_names or "No specific pest guidance retrieved.",
            "why": "Grounded in the retrieved pest/disease control material for this crop.",
            "quantity": None,
            "cost": items_by_label.get("Pest & Disease Control", 0),
            "organicAlternative": None,
        },
        {
            "id": "harvest",
            "name": "Harvest",
            "date": _window_text(season_plan.get("harvest_window")),
            "what": "Harvest when the crop reaches full maturity.",
            "why": season_plan.get("reasoning", ""),
            "quantity": f"Expected yield ~{season_plan.get('expected_yield_ton_per_acre', '?')} tons/acre",
            "cost": items_by_label.get("Labor", 0) + items_by_label.get("Post-harvest & Transport", 0),
            "organicAlternative": None,
        },
    ]


def serialize_knowledge_sources(retrieved_docs: list[dict]) -> list[dict]:
    """Each entry is `{label, url}` — `url` is only ever present for a web
    search fallback result (see `tools/web_search.py`); a knowledge-base
    citation has `url: None` and the frontend renders it as plain text
    instead of a link, so the two are visually distinguishable."""
    seen: dict[str, dict] = {}
    for doc in retrieved_docs:
        if doc.get("url"):
            label = doc["source_title"]
            url = doc["url"]
        else:
            label = (
                f"{doc['source_title']} (p.{doc['page_number']})"
                if doc.get("page_number")
                else doc["source_title"]
            )
            url = None
        if label not in seen:
            seen[label] = {"label": label, "url": url}
    return list(seen.values())


def serialize_messages(messages: list) -> list[dict]:
    from langchain_core.messages import AIMessage, HumanMessage

    out = []
    for i, m in enumerate(messages):
        if isinstance(m, HumanMessage):
            role = "user"
        elif isinstance(m, AIMessage):
            role = "assistant"
        else:
            continue
        if not m.content:
            continue
        entry = {"id": f"m-{i}", "role": role, "text": m.content}
        # Cross-verified/tentative disease-diagnosis badge — see
        # nodes/disease_explanation.py, which is the only node that sets it.
        badge = isinstance(m, AIMessage) and m.additional_kwargs.get("badge")
        if badge:
            entry["badge"] = badge
        out.append(entry)
    return out
