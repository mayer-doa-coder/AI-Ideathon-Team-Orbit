"""Open-Meteo geocoding + forecast — real HTTP calls, keyless, no API key
required.

Two independent implementations live here, not yet unified (same split as
`tools/financials.py`, see that file's docstring for why):

- `geocode_location` / `get_weather_forecast` — the conversation agent's
  versions. Return `None` on any failure (timeout, non-2xx, no match) so
  callers must handle absence explicitly; forecast result is parallel
  arrays (`dates`, `daily_rainfall_mm`, ...).
- `monitor_geocode_location` / `monitor_get_weather_forecast` — the monitor
  graph's versions. Raise `WeatherAPIError` on failure instead of returning
  `None`, so a failed call can't silently be treated as "no rain forecast"
  by `compare_thresholds`; forecast result is a `ForecastResult` (list of
  per-day dicts), and `get_weather_forecast` takes a `days` param.

Both are real, keyless Open-Meteo calls for the forecast itself — no
invented weather data either way. District-level place-name resolution,
though, is answered from `BD_DISTRICT_COORDS` first (see below) rather than
trusting the live geocoder, which has real, unpredictable gaps for
Bangladesh.
"""
import re
import time
from typing import TypedDict

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CACHE_TTL_SECONDS = 1800
REQUEST_TIMEOUT = 10.0

_geocode_cache: dict[str, tuple[float, dict]] = {}
_forecast_cache: dict[str, tuple[float, dict]] = {}

# Every one of Bangladesh's 64 districts, by division, as the *exact*,
# authoritative answer for a district-level place name — not a fallback on
# top of live geocoding, the first thing checked. This exists because
# Open-Meteo's gazetteer has real, silent gaps for Bangladesh: it doesn't
# recognize the 2018 district renames, so searching "Bogura" matches an
# unrelated village in Rostov Oblast, Russia (~4900km away, no error, just
# a wrong answer) and "Cumilla" matches nothing at all. Rather than patch
# each rename as it's discovered, every district is hardcoded once here —
# a live geocoding call is a courtesy for names outside this table (an
# upazila, a bazar, a typo), not something a known BD district should ever
# depend on succeeding correctly.
#
# Coordinates are district-town/sadar-level (good enough for regional
# distance ranking, not a precise GPS point), cross-checked against
# Open-Meteo's own geocoder for every district that resolves correctly
# there; the ones it gets wrong or misses (Bogura, Cumilla, Chattogram,
# Jashore, Barishal) are the value actually confirmed for their real
# Bangladeshi location under the alias Open-Meteo does recognize.
# Dict keys are punctuation/space-stripped lowercase (see
# `_normalize_place_name`) so "Cox's Bazar" and "Coxs Bazar" both hit.
BD_DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    # Dhaka division
    "dhaka": (23.7104, 90.4074),
    "faridpur": (23.6070, 89.8429),
    "gazipur": (23.9999, 90.4203),
    "gopalganj": (23.0050, 89.8266),
    "kishoreganj": (24.4449, 90.7766),
    "madaripur": (23.1641, 90.1897),
    "manikganj": (23.8644, 90.0047),
    "munshiganj": (23.5422, 90.5305),
    "narayanganj": (23.6238, 90.5000),
    "narsingdi": (23.9322, 90.7150),
    "rajbari": (23.7574, 89.6444),
    "shariatpur": (23.2423, 90.4348),
    "tangail": (24.2513, 89.9167),
    # Chattogram division
    "bandarban": (22.1953, 92.2184),
    "brahmanbaria": (23.9571, 91.1119),
    "chandpur": (23.2333, 90.6417),
    "chattogram": (22.3384, 91.8317),
    "chittagong": (22.3384, 91.8317),  # pre-2018 name
    "cumilla": (23.4619, 91.1850),
    "comilla": (23.4619, 91.1850),  # pre-2018 name
    "coxsbazar": (21.4272, 92.0058),
    "feni": (23.0159, 91.3976),
    "khagrachhari": (23.1193, 91.9847),
    "lakshmipur": (22.9440, 90.8282),
    "noakhali": (22.8696, 91.0995),
    "rangamati": (22.6533, 92.1787),
    # Rajshahi division
    "bogura": (24.8510, 89.3711),
    "bogra": (24.8510, 89.3711),  # pre-2018 name
    "joypurhat": (25.0968, 89.0227),
    "naogaon": (24.7936, 88.9318),
    "natore": (24.4206, 88.9865),
    "chapainawabganj": (24.5965, 88.2775),
    "pabna": (24.0064, 89.2372),
    "rajshahi": (24.3745, 88.6042),
    "sirajganj": (24.4533, 89.7006),
    # Khulna division
    "bagerhat": (22.6602, 89.7895),
    "chuadanga": (23.6402, 88.8410),
    "jashore": (23.1697, 89.2137),
    "jessore": (23.1697, 89.2137),  # pre-2018 name
    "jhenaidah": (23.5450, 89.1539),
    "khulna": (22.8098, 89.5644),
    "kushtia": (23.9013, 89.1206),
    "magura": (23.4855, 89.4198),
    "meherpur": (23.7622, 88.6318),
    "narail": (23.1725, 89.5126),
    "satkhira": (22.7085, 89.0714),
    # Barishal division
    "barguna": (22.0953, 90.1121),
    "barishal": (22.7050, 90.3701),
    "barisal": (22.7050, 90.3701),  # common alternate spelling
    "bhola": (22.6859, 90.6482),
    "jhalokati": (22.6406, 90.1987),
    "patuakhali": (22.3596, 90.3296),
    "pirojpur": (22.5841, 89.9720),
    # Sylhet division
    "habiganj": (24.3745, 91.4155),
    "moulvibazar": (24.4829, 91.7774),
    "sunamganj": (25.0658, 91.3950),
    "sylhet": (24.8990, 91.8720),
    # Rangpur division
    "dinajpur": (25.6217, 88.6354),
    "gaibandha": (25.3288, 89.5289),
    "kurigram": (25.8054, 89.6362),
    "lalmonirhat": (25.9923, 89.2847),
    "nilphamari": (25.9317, 88.8560),
    "panchagarh": (26.3411, 88.5541),
    "rangpur": (25.7466, 89.2517),
    "thakurgaon": (26.0336, 88.4616),
    # Mymensingh division
    "jamalpur": (24.9375, 89.9372),
    "mymensingh": (24.7564, 90.4065),
    "netrokona": (24.8709, 90.7276),
    "sherpur": (25.0204, 90.0153),
}


def _normalize_place_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.strip().lower())


def _lookup_bd_district(name: str) -> tuple[float, float] | None:
    return BD_DISTRICT_COORDS.get(_normalize_place_name(name))


def _bd_geocode_search(location: str, timeout: float) -> dict | None:
    """Live fallback for place names *not* in `BD_DISTRICT_COORDS` — an
    upazila, a bazar name, a spelling this module doesn't know about. Still
    restricted to Bangladesh (this app only serves Bangladeshi farmers, so a
    match in another country is never correct — it's exactly how "Bogura"
    silently matched a village in Russia before the exact table existed)."""
    response = httpx.get(
        GEOCODING_URL,
        params={"name": location, "count": 1, "language": "en", "format": "json"},
        timeout=timeout,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    top = results[0] if results else None

    if top is not None and top.get("country") == "Bangladesh":
        return top
    return None


def _cache_get(cache: dict, key: str) -> dict | None:
    entry = cache.get(key)
    if not entry:
        return None
    cached_at, value = entry
    if time.time() - cached_at > CACHE_TTL_SECONDS:
        cache.pop(key, None)
        return None
    return value


def geocode_location(location: str) -> dict | None:
    key = location.strip().lower()
    cached = _cache_get(_geocode_cache, key)
    if cached is not None:
        return cached

    exact = _lookup_bd_district(location)
    if exact:
        lat, lon = exact
        result = {"lat": lat, "lon": lon, "resolved_name": location.strip(), "country": "Bangladesh", "admin1": None}
        _geocode_cache[key] = (time.time(), result)
        return result

    try:
        top = _bd_geocode_search(location, REQUEST_TIMEOUT)
    except httpx.HTTPError:
        return None

    if top is None:
        return None

    result = {
        "lat": top["latitude"],
        "lon": top["longitude"],
        "resolved_name": top.get("name"),
        "country": top.get("country"),
        "admin1": top.get("admin1"),
    }
    _geocode_cache[key] = (time.time(), result)
    return result


def get_weather_forecast(lat: float, lon: float) -> dict | None:
    key = f"{round(lat, 2)},{round(lon, 2)}"
    cached = _cache_get(_forecast_cache, key)
    if cached is not None:
        return cached

    try:
        response = httpx.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "forecast_days": 14,
                "timezone": "auto",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        daily = response.json().get("daily") or {}
    except httpx.HTTPError:
        return None

    dates = daily.get("time") or []
    if not dates:
        return None

    result = {
        "dates": dates,
        "daily_rainfall_mm": daily.get("precipitation_sum") or [],
        "daily_temp_max_c": daily.get("temperature_2m_max") or [],
        "daily_temp_min_c": daily.get("temperature_2m_min") or [],
    }
    _forecast_cache[key] = (time.time(), result)
    return result


MONITOR_GEOCODE_CACHE_TTL_SECONDS = 3600
MONITOR_FORECAST_CACHE_TTL_SECONDS = 1800
MONITOR_REQUEST_TIMEOUT_SECONDS = 10
MONITOR_DEFAULT_FORECAST_DAYS = 14

_monitor_geocode_cache: dict[str, tuple[float, dict]] = {}
_monitor_forecast_cache: dict[tuple[float, float, int], tuple[float, dict]] = {}


class WeatherAPIError(Exception):
    """Raised when Open-Meteo can't be reached or returns nothing usable."""


class GeocodeResult(TypedDict):
    resolved_name: str
    country: str
    lat: float
    lon: float


class DailyForecast(TypedDict):
    date: str
    rainfall_mm: float
    temp_max_c: float
    temp_min_c: float


class ForecastResult(TypedDict):
    lat: float
    lon: float
    daily: list[DailyForecast]


def monitor_geocode_location(place_name: str) -> GeocodeResult:
    """Resolve a free-text place name (e.g. "Rajshahi") to lat/lon."""
    cache_key = place_name.strip().lower()
    cached = _monitor_geocode_cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < MONITOR_GEOCODE_CACHE_TTL_SECONDS:
        return cached[1]

    exact = _lookup_bd_district(place_name)
    if exact:
        lat, lon = exact
        result: GeocodeResult = {
            "resolved_name": place_name.strip(),
            "country": "Bangladesh",
            "lat": lat,
            "lon": lon,
        }
        _monitor_geocode_cache[cache_key] = (time.monotonic(), result)
        return result

    try:
        top = _bd_geocode_search(place_name, MONITOR_REQUEST_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise WeatherAPIError(f"Geocoding request failed for '{place_name}': {exc}") from exc

    if top is None:
        raise WeatherAPIError(f"No geocoding match found for '{place_name}'")

    result: GeocodeResult = {
        "resolved_name": top["name"],
        "country": top.get("country", ""),
        "lat": top["latitude"],
        "lon": top["longitude"],
    }
    _monitor_geocode_cache[cache_key] = (time.monotonic(), result)
    return result


def monitor_get_weather_forecast(
    lat: float, lon: float, days: int = MONITOR_DEFAULT_FORECAST_DAYS
) -> ForecastResult:
    """Real daily rainfall + temperature forecast for a coordinate."""
    cache_key = (round(lat, 3), round(lon, 3), days)
    cached = _monitor_forecast_cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < MONITOR_FORECAST_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        response = httpx.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=MONITOR_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise WeatherAPIError(f"Forecast request failed for ({lat}, {lon}): {exc}") from exc

    daily = payload.get("daily")
    if not daily or not daily.get("time"):
        raise WeatherAPIError(f"Forecast response had no daily data for ({lat}, {lon})")

    result: ForecastResult = {
        "lat": lat,
        "lon": lon,
        "daily": [
            {
                "date": date,
                "rainfall_mm": rainfall if rainfall is not None else 0.0,
                "temp_max_c": tmax,
                "temp_min_c": tmin,
            }
            for date, rainfall, tmax, tmin in zip(
                daily["time"],
                daily["precipitation_sum"],
                daily["temperature_2m_max"],
                daily["temperature_2m_min"],
            )
        ],
    }
    _monitor_forecast_cache[cache_key] = (time.monotonic(), result)
    return result
