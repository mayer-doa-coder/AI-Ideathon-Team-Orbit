"""Tier 2: finds and ranks suppliers for an agricultural input the farmer
wants to buy, using the seeded supplier catalog (`tools/marketplace.py`).
Structured Postgres lookup, not a RAG retrieval — no LLM call needed here,
the extraction already happened in `classify_intent`."""
from langchain_core.messages import AIMessage

from app.agents.state import AgentState
from app.db.session import SessionLocal
from app.tools.marketplace import MarketplaceSearchResult, search_and_rank_suppliers
from app.tools.weather import geocode_location

TOP_N_DISPLAYED = 3


def _resolve_search(
    query: dict, profile: dict, current_location: dict | None, trace: list[dict]
) -> tuple[str | None, float | None, float | None, str | None]:
    """Decide (a) which district to restrict the catalog search to, and (b)
    the point distance should be measured from — and what to call that
    point in the reply. Priority, most to least specific:

    1. A district the farmer actually named this turn — always resolved
       for real (never overridden by farm/current location, even if we
       already know those), otherwise asking about Sylhet while the farm's
       own coordinates happen to be cached would silently rank by distance
       from the farm instead of from Sylhet.
    2. The farmer's current browser location ("near me" — no named
       district) — ranks the *whole* catalog by real distance rather than
       silently restricting to whatever district the farm happens to be
       registered in, which is a different question than "near me".
    3. The farm's own registered location — coordinates if we have them,
       else its location text, geocoded, as the pre-existing fallback.
    """
    explicit_district = query.get("district")
    if explicit_district:
        geo = geocode_location(explicit_district)
        trace.append(
            {
                "type": "marketplace",
                "tool": "geocode_location",
                "paramsDisplay": f'location="{explicit_district}"',
                "params": {"location": explicit_district},
                "response": geo or {"error": "geocoding failed"},
                "summary": (
                    f"resolved {explicit_district} to {geo['resolved_name']}, {geo.get('admin1', '')}"
                    if geo
                    else f"could not resolve '{explicit_district}' — falling back to price/rating ranking"
                ),
            }
        )
        ref = (geo["lat"], geo["lon"]) if geo else (None, None)
        return explicit_district, ref[0], ref[1], explicit_district

    if current_location:
        return None, current_location["lat"], current_location["lon"], "your current location"

    farm_location = profile.get("location")
    farm_lat, farm_lon = profile.get("lat"), profile.get("lon")
    if farm_lat is not None and farm_lon is not None:
        return farm_location, farm_lat, farm_lon, farm_location
    if farm_location:
        geo = geocode_location(farm_location)
        return farm_location, (geo["lat"] if geo else None), (geo["lon"] if geo else None), farm_location

    return None, None, None, None


def _format_offer_line(rank: int, o) -> str:
    distance_part = f", {o.distance_km:.0f} km away" if o.distance_km is not None else ""
    return (
        f"{rank}. **{o.business_name}** ({o.district}{distance_part}) — "
        f"৳{o.price_bdt_per_unit:.0f}/{o.unit}, {o.stock_available:.0f}{o.unit} in stock, "
        f"delivery in {o.delivery_days}d, rated {o.rating:.1f}/5. "
        f"_{'; '.join(o.reasons)}._"
    )


def marketplace_lookup(state: AgentState) -> dict:
    query = state.get("marketplace_query") or {}
    profile = state.get("farm_profile") or {}
    product = query.get("product")

    if not product:
        return {
            "turn_complete": True,
            "messages": [
                AIMessage(content="Which input are you looking for — e.g. urea, DAP, or a pesticide?")
            ],
        }

    quantity_kg = query.get("quantity_kg")

    trace: list[dict] = []
    district, ref_lat, ref_lon, place_label = _resolve_search(query, profile, state.get("current_location"), trace)

    db = SessionLocal()
    try:
        result: MarketplaceSearchResult = search_and_rank_suppliers(
            db, product=product, district=district, quantity=quantity_kg, ref_lat=ref_lat, ref_lon=ref_lon
        )
    finally:
        db.close()

    offers = result.offers
    trace.append(
        {
            "type": "marketplace",
            "tool": "search_and_rank_suppliers",
            "paramsDisplay": f'product="{product}", district={district or "any"}, quantity_kg={quantity_kg or "any"}',
            "params": {"product": product, "district": district, "quantity_kg": quantity_kg},
            "response": {
                "matches": len(offers),
                "matched_district": result.matched_district,
                "ranked_by_distance": result.ranked_by_distance,
                "ranked": [
                    {
                        "supplier": o.business_name,
                        "district": o.district,
                        "distance_km": o.distance_km,
                        "price_bdt_per_unit": o.price_bdt_per_unit,
                        "score": o.score,
                        "reasons": o.reasons,
                    }
                    for o in offers[:5]
                ],
            },
            "summary": (
                f"{len(offers)} supplier offer(s) found for {product}" if offers else f"no suppliers found for {product}"
            ),
        }
    )

    if not offers:
        near = f" near {place_label}" if place_label else ""
        message = (
            f"I couldn't find any suppliers for \"{product}\"{near} in the catalog yet. "
            f"Try a different product name, or check back as more suppliers get added."
        )
        return {"trace_log": trace, "turn_complete": True, "messages": [AIMessage(content=message)]}

    lines: list[str]
    if result.matched_district:
        near = f" near {place_label}" if place_label else ""
        lines = [f"Here's what I found for **{product}**{near}:"]
    elif result.ranked_by_distance:
        lines = [
            f"No supplier lists **{product}** near {place_label} yet — here's the nearest available option instead:"
        ]
    else:
        lines = [
            f"No supplier lists **{product}** near {place_label} yet, and I couldn't work out distances to rank by "
            f"proximity — here are the best matches by price and rating instead:"
        ]

    for i, o in enumerate(offers[:TOP_N_DISPLAYED], 1):
        lines.append(_format_offer_line(i, o))

    top = offers[0]
    if len(offers) > 1:
        lines.append(f"\nI'd recommend **{top.business_name}** — {'; '.join(top.reasons)}.")
    if top.phone:
        lines.append(f"Contact: {top.phone}. Call ahead to confirm current stock before heading out.")

    return {
        "trace_log": trace,
        "turn_complete": True,
        "messages": [AIMessage(content="\n".join(lines))],
    }
