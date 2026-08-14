"""Entry node: get the forecast this sweep will reason over.

Real Open-Meteo call, unless a `weather_override` is present — that only
happens on the `simulate-trigger` demo endpoint, which injects a synthetic
forecast so a judge can see the trigger fire on demand without waiting for
real weather to cooperate. Every downstream node treats both cases
identically; only where the forecast comes from differs.
"""
from app.agents.state import MonitorState
from app.db.trace import log_trace
from app.tools.weather import WeatherAPIError, monitor_get_weather_forecast

FORECAST_DAYS = 14


def fetch_weather(state: MonitorState) -> dict:
    if state.get("weather_override"):
        weather_data = state["weather_override"]
        log_trace(
            farm_id=state["farm_id"],
            source="monitor",
            node_name="fetch_weather",
            tool_name="weather_override",
            params={"note": "simulate-trigger: synthetic forecast, not a real API call"},
            result={"daily_count": len(weather_data.get("daily", []))},
        )
        return {"weather_data": weather_data}

    farm = state["farm"]
    try:
        weather_data = monitor_get_weather_forecast(farm["lat"], farm["lon"], days=FORECAST_DAYS)
    except WeatherAPIError as exc:
        log_trace(
            farm_id=state["farm_id"],
            source="monitor",
            node_name="fetch_weather",
            tool_name="monitor_get_weather_forecast",
            params={"lat": farm["lat"], "lon": farm["lon"], "days": FORECAST_DAYS},
            result={"error": str(exc)},
        )
        return {"weather_data": None}

    log_trace(
        farm_id=state["farm_id"],
        source="monitor",
        node_name="fetch_weather",
        tool_name="monitor_get_weather_forecast",
        params={"lat": farm["lat"], "lon": farm["lon"], "days": FORECAST_DAYS},
        result={"daily": weather_data["daily"][:3], "daily_count": len(weather_data["daily"])},
    )
    return {"weather_data": weather_data}
