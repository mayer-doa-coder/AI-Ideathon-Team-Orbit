"""On-demand entry points into the same monitor graph the scheduler runs
automatically every `MONITOR_INTERVAL_HOURS` — for genuine ad-hoc checks
(`check-weather-now`) and for reliably demoing a trigger in front of judges
without waiting on real weather to cooperate (`simulate-trigger`).
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.graph_monitor import run_monitor_sweep
from app.agents.state import MonitorState
from app.api.deps import get_current_user
from app.db.models import Farm
from app.db.session import get_db
from app.models.user import User
from app.schemas.monitor import MonitorSweepResponse, SimulateTriggerRequest

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


def _get_owned_farm(db: Session, farm_id: int, user: User) -> Farm:
    farm = db.get(Farm, farm_id)
    if farm is None or farm.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


def _default_heavy_rain_override() -> dict:
    """Synthetic 14-day forecast with a heavy-rain spike on days 1-2 —
    reliably trips the runoff/pest thresholds regardless of real weather,
    exactly the "clearly labeled as test data" demo path from the spec."""
    today = date.today()
    daily = []
    for i in range(14):
        rainfall = 45.0 if i in (1, 2) else 4.0
        daily.append(
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "rainfall_mm": rainfall,
                "temp_max_c": 33.0,
                "temp_min_c": 26.0,
            }
        )
    return {"lat": None, "lon": None, "daily": daily}


def _to_response(result: MonitorState, simulated: bool) -> MonitorSweepResponse:
    return MonitorSweepResponse(
        farm_id=result["farm_id"],
        simulated=simulated,
        triggered=result["triggered"],
        trigger_reason=result.get("trigger_reason"),
        weather_data=result.get("weather_data"),
        updated_plan=result.get("updated_plan"),
        updated_financials=result.get("updated_financials"),
    )


@router.post("/check-weather-now/{farm_id}", response_model=MonitorSweepResponse)
def check_weather_now(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Real Open-Meteo call, same graph as the scheduled sweep."""
    _get_owned_farm(db, farm_id, current_user)
    result = run_monitor_sweep(db, farm_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This farm has no committed season plan yet — nothing to monitor.",
        )
    return _to_response(result, simulated=False)


@router.post("/simulate-trigger/{farm_id}", response_model=MonitorSweepResponse)
def simulate_trigger(
    farm_id: int,
    payload: SimulateTriggerRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Injects a synthetic forecast via `weather_override`; every downstream
    node runs the identical real logic. This is test data, not live weather."""
    _get_owned_farm(db, farm_id, current_user)
    override = (payload.weather_override if payload else None) or _default_heavy_rain_override()
    result = run_monitor_sweep(db, farm_id, weather_override=override)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This farm has no committed season plan yet — nothing to monitor.",
        )
    return _to_response(result, simulated=True)
