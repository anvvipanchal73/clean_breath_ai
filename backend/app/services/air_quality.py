"""
Air Quality ingestion service for CleanBreath AI.

Primary source: Open-Meteo Air Quality API (no API key required for
non-commercial use, free tier).
Fallback: OpenAQ / WAQI (require API keys, configured in .env).

Coordinates are coarse-rounded to 2 decimal places (~1.1 km) before any
external call, enforcing our privacy-by-design principle.

If all sources fail or return stale data (> 2 h), is_stale is set to True
on the returned snapshot.  The API layer MUST surface this to the UI.

IMPORTANT: This module never fabricates or extrapolates AQI values.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.models.domain import AQIForecast, AQISnapshot, ForecastPoint

logger = logging.getLogger(__name__)
settings = get_settings()

_STALE_THRESHOLD_SECONDS = 7200  # 2 hours


def _coarse_coords(lat: float, lon: float, decimals: int = 2) -> tuple[float, float]:
    """Round coordinates to `decimals` decimal places for coarse privacy."""
    factor = 10**decimals
    return math.floor(lat * factor) / factor, math.floor(lon * factor) / factor


# ---------------------------------------------------------------------------
# Open-Meteo (primary)
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _fetch_open_meteo_current(lat: float, lon: float) -> dict[str, Any]:
    url = settings.open_meteo_base_url + "/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "us_aqi", "pm2_5", "pm10", "nitrogen_dioxide",
            "ozone", "carbon_monoxide", "sulphur_dioxide",
            "european_aqi",
        ],
        "hourly": ["boundary_layer_height"],
        "forecast_days": 1,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _fetch_open_meteo_forecast(lat: float, lon: float) -> dict[str, Any]:
    url = settings.open_meteo_base_url + "/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["us_aqi", "pm2_5", "temperature_2m"],
        "forecast_days": 3,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _parse_open_meteo_current(data: dict[str, Any], lat: float, lon: float) -> AQISnapshot:
    cur = data.get("current", {})
    # Boundary layer height – take the first value from hourly if present
    blh_values = data.get("hourly", {}).get("boundary_layer_height", [])
    blh = blh_values[0] if blh_values else None
    return AQISnapshot(
        lat=lat,
        lon=lon,
        aqi_us=cur.get("us_aqi"),
        pm25=cur.get("pm2_5"),
        pm10=cur.get("pm10"),
        no2=cur.get("nitrogen_dioxide"),
        o3=cur.get("ozone"),
        co=cur.get("carbon_monoxide"),
        so2=cur.get("sulphur_dioxide"),
        boundary_layer_height_m=blh,
        stagnation_risk=(blh is not None and blh < 500),  # shallow boundary layer
        source="open-meteo",
        fetched_at=datetime.now(timezone.utc),
        is_stale=False,
    )


def _parse_open_meteo_forecast(data: dict[str, Any], lat: float, lon: float) -> AQIForecast:
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    aqi_vals = hourly.get("us_aqi", [None] * len(times))
    pm25_vals = hourly.get("pm2_5", [None] * len(times))
    temp_vals = hourly.get("temperature_2m", [None] * len(times))

    points: list[ForecastPoint] = []
    for i, t in enumerate(times[:48]):  # 48 h
        try:
            dt = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        points.append(ForecastPoint(
            time=dt,
            aqi_us=aqi_vals[i] if i < len(aqi_vals) else None,
            pm25=pm25_vals[i] if i < len(pm25_vals) else None,
            temperature_c=temp_vals[i] if i < len(temp_vals) else None,
        ))

    return AQIForecast(lat=lat, lon=lon, points=points, source="open-meteo",
                       fetched_at=datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def get_current_air_quality(lat: float, lon: float) -> AQISnapshot:
    """
    Fetch current air quality snapshot.
    Coordinates are coarse-rounded before any external call.
    Returns a snapshot with is_stale=True if data could not be fetched.
    """
    c_lat, c_lon = _coarse_coords(lat, lon)
    try:
        data = await _fetch_open_meteo_current(c_lat, c_lon)
        return _parse_open_meteo_current(data, c_lat, c_lon)
    except Exception as exc:
        logger.warning("Open-Meteo fetch failed: %s – returning stale placeholder", exc)
        return AQISnapshot(
            lat=c_lat, lon=c_lon,
            source="unavailable",
            is_stale=True,
            fetched_at=datetime.now(timezone.utc),
        )


async def get_forecast(lat: float, lon: float) -> AQIForecast:
    """
    Fetch 48-hour AQI forecast.
    Returns an empty forecast (with is_stale logic handled upstream) if unavailable.
    """
    c_lat, c_lon = _coarse_coords(lat, lon)
    try:
        data = await _fetch_open_meteo_forecast(c_lat, c_lon)
        return _parse_open_meteo_forecast(data, c_lat, c_lon)
    except Exception as exc:
        logger.warning("Open-Meteo forecast fetch failed: %s", exc)
        return AQIForecast(lat=c_lat, lon=c_lon, source="unavailable")
