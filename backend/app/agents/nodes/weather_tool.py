from app.agents.state import AgentState
from app.tools.weather import geocode_location, get_weather_forecast


def weather_tool(state: AgentState) -> dict:
    profile = state.get("farm_profile") or {}
    location = profile.get("location")
    if not location:
        return {}

    trace = []
    lat, lon = profile.get("lat"), profile.get("lon")
    profile_update: dict = {}

    if lat is None or lon is None:
        geo = geocode_location(location)
        trace.append(
            {
                "type": "weather",
                "tool": "geocode_location",
                "paramsDisplay": f'location="{location}"',
                "params": {"location": location},
                "response": geo or {"error": "geocoding failed"},
                "summary": (
                    f"resolved to {geo['resolved_name']}, {geo.get('admin1', '')}"
                    if geo
                    else "could not resolve this location"
                ),
            }
        )
        if not geo:
            return {"trace_log": trace}
        lat, lon = geo["lat"], geo["lon"]
        profile_update = {"lat": lat, "lon": lon}

    forecast = get_weather_forecast(lat, lon)
    trace.append(
        {
            "type": "weather",
            "tool": "get_weather_forecast",
            "paramsDisplay": f"lat={lat}, lon={lon}",
            "params": {"lat": lat, "lon": lon},
            "response": forecast or {"error": "forecast unavailable"},
            "summary": (
                f"{len(forecast['dates'])}-day forecast retrieved, "
                f"{sum(forecast['daily_rainfall_mm']):.0f}mm total rainfall"
                if forecast
                else "weather service unavailable — proceeding without a forecast"
            ),
        }
    )

    update: dict = {"trace_log": trace}
    if profile_update:
        update["farm_profile"] = {**profile, **profile_update}
    if forecast:
        update["weather_data"] = forecast
    return update
