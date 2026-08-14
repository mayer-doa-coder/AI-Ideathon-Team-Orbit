"""CLI: seed one farm + a committed season plan so the monitor agent (and
the dashboard) have something real to work against, without needing the
conversation agent's onboarding flow to be finished first.

Usage (from /app inside the backend container, or the backend/ venv):
    python -m scripts.seed_demo_farm
    python -m scripts.seed_demo_farm --username demo_farmer --location Rangpur --acres 3 --crop Rice
"""
import argparse
from datetime import date, timedelta

from app.db.models import Farm, Plan
from app.db.session import SessionLocal
from app.services.user_service import create_user, get_user_by_username
from app.tools.financials import calculate_financials
from app.tools.weather import WeatherAPIError, monitor_geocode_location

# Static fallback so seeding never depends on network access — these are
# the same four options the frontend's onboarding step offers.
KNOWN_LOCATIONS = {
    "rajshahi": (24.3745, 88.6042),
    "dhaka": (23.8103, 90.4125),
    "khulna": (22.8456, 89.5403),
    "rangpur": (25.7439, 89.2752),
}

DEFAULT_USERNAME = "demo_farmer"
DEFAULT_PASSWORD = "demo12345"
DEFAULT_LOCATION = "Rajshahi"
DEFAULT_ACRES = 2.0
DEFAULT_CROP = "Rice"


def resolve_location(location: str) -> tuple[float, float]:
    known = KNOWN_LOCATIONS.get(location.strip().lower())
    if known:
        return known
    try:
        result = monitor_geocode_location(location)
        return result["lat"], result["lon"]
    except WeatherAPIError as exc:
        raise SystemExit(
            f"Couldn't resolve '{location}' (not in the known list and geocoding failed: {exc})"
        )


def build_season_plan(crop: str) -> dict:
    """Dated relative to today so the monitor's lookahead windows have a
    pending item to react to regardless of which day this is run."""
    today = date.today()

    def d(offset: int) -> str:
        return (today + timedelta(days=offset)).isoformat()

    return {
        "crop": crop,
        "sowing_window": {"start": d(-10), "end": d(2)},
        "fertilizer_schedule": [
            {
                "name": "Urea (1st split - basal)", "stage": "basal", "date": d(-3),
                "amount_kg_per_acre": 25, "status": "applied", "adjusted": False,
                "adjustment_note": None, "date_before_adjustment": None,
            },
            {
                "name": "Urea (2nd split - tillering)", "stage": "tillering", "date": d(3),
                "amount_kg_per_acre": 25, "status": "pending", "adjusted": False,
                "adjustment_note": None, "date_before_adjustment": None,
            },
            {
                "name": "Urea (3rd split - panicle initiation)", "stage": "panicle_initiation",
                "date": d(25), "amount_kg_per_acre": 25, "status": "pending", "adjusted": False,
                "adjustment_note": None, "date_before_adjustment": None,
            },
        ],
        "irrigation_schedule": [
            {"date": d(1), "note": "Maintain 2-4cm standing water", "status": "pending"},
            {"date": d(10), "note": "Drain field before topdressing", "status": "pending"},
        ],
        "pest_risks": [
            {
                "name": "Bacterial leaf blight", "risk_window_start": d(2), "risk_window_end": d(20),
                "status": "watching", "adjusted": False, "adjustment_note": None,
                "prevention": "Use resistant varieties, avoid excess nitrogen, ensure good field drainage.",
            },
            {
                "name": "Brown planthopper", "risk_window_start": d(30), "risk_window_end": d(45),
                "status": "watching", "adjusted": False, "adjustment_note": None,
                "prevention": "Avoid excess nitrogen, maintain proper plant spacing, monitor and treat early.",
            },
        ],
        "weed_checkpoints": [{"date": d(15), "note": "First hand weeding / herbicide check"}],
        "harvest_window": {"start": d(95), "end": d(110)},
        "seed_rate_kg_per_acre": 8.0,
        "expected_yield_ton_per_acre": 2.5,
        "reasoning": "Seeded demo plan for judge-demo reliability — illustrative, not RAG-grounded.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a demo farm + committed season plan")
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--acres", type=float, default=DEFAULT_ACRES)
    parser.add_argument("--soil-type", default="Loamy")
    parser.add_argument("--water-availability", default="Medium")
    parser.add_argument("--budget", type=float, default=50000.0)
    parser.add_argument("--season", default="Summer")
    parser.add_argument("--crop", default=DEFAULT_CROP)
    args = parser.parse_args()

    lat, lon = resolve_location(args.location)

    db = SessionLocal()
    try:
        user = get_user_by_username(db, args.username)
        if user is None:
            user = create_user(db, args.username, args.password)
            print(f"Created user '{args.username}' (password: {args.password})")
        else:
            print(f"Using existing user '{args.username}'")

        farm = db.query(Farm).filter(Farm.user_id == user.id).one_or_none()
        if farm is None:
            farm = Farm(
                user_id=user.id,
                location=args.location,
                lat=lat,
                lon=lon,
                acres=args.acres,
                soil_type=args.soil_type,
                water_availability=args.water_availability,
                budget=args.budget,
                season=args.season,
            )
            db.add(farm)
            db.commit()
            db.refresh(farm)
            print(f"Created farm id={farm.id} at {args.location} ({lat}, {lon})")
        else:
            print(f"Using existing farm id={farm.id} at {farm.location}")

        season_plan = build_season_plan(args.crop)
        financials = calculate_financials(season_plan, args.crop, args.acres)

        plan = db.query(Plan).filter(Plan.farm_id == farm.id).one_or_none()
        if plan is None:
            plan = Plan(farm_id=farm.id, selected_crop=args.crop, season_plan=season_plan, financials=financials)
            db.add(plan)
        else:
            plan.selected_crop = args.crop
            plan.season_plan = season_plan
            plan.financials = financials
        db.commit()

        print(f"Committed plan for farm id={farm.id}: {args.crop} on {args.acres} acres")
        print(f"Net profit estimate: {financials['profit']} BDT (ROI {financials['roi']}%)")
        print(
            f"\nTry it:\n"
            f"  POST /api/monitor/check-weather-now/{farm.id}\n"
            f"  POST /api/monitor/simulate-trigger/{farm.id}\n"
            f"  GET  /api/alerts?farm_id={farm.id}\n"
            f"  GET  /api/trace/{farm.id}\n"
            f"(login as '{args.username}' first to get a bearer token)"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
