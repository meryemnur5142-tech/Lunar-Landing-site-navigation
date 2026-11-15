"""
GET /forecast — time-dependent lunar landing window forecast via JPL Horizons.

Query params:
  crater_id  : tycho | copernicus | clavius
  dt         : ISO-8601 UTC datetime, e.g. 2027-03-15T12:00:00Z

Returns for each of the 7 zones:
  solar_elevation_deg  — Sun above/below horizon (> 0 = lit)
  earth_elevation_deg  — Earth above/below horizon (> 0 = direct comms)
  solar_lit            — bool
  earth_visible        — bool
  optimal_solar        — bool  (10–45° — good for solar-powered rover)
  forecast_note        — short human-readable status string
"""

from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/forecast", tags=["forecast"])

# ── Mirror of dist/data.js fixtures ────────────────────────────────────────

_CRATERS = {
    "tycho":      {"lat": -43.31, "lon": -11.36, "shift": 0},
    "copernicus": {"lat":   9.62, "lon": -20.08, "shift": 1},
    "clavius":    {"lat": -58.75, "lon": -14.40, "shift": 2},
}

_FIXTURES = [
    {"id": "A", "x":  8, "y":  3},
    {"id": "B", "x": 11, "y":  5},
    {"id": "C", "x":  7, "y":  6},
    {"id": "D", "x": 14, "y":  4},
    {"id": "E", "x": 10, "y":  9},
    {"id": "F", "x":  6, "y": 10},
    {"id": "G", "x": 15, "y": 11},
]


def _zone_lat_lon(crater: dict, fx: dict) -> tuple[float, float]:
    shift = crater["shift"]
    x = fx["x"] + shift
    y = fx["y"] + shift * 0.5
    lat = crater["lat"] + math.degrees(y / 1737.4)
    lon = crater["lon"] + math.degrees(x / (1737.4 * math.cos(math.radians(crater["lat"]))))
    return lat, lon


# ── Response schema ─────────────────────────────────────────────────────────

class ZoneForecast(BaseModel):
    zone_id: str
    lat: float
    lon: float
    solar_elevation_deg: float
    earth_elevation_deg: float
    solar_lit: bool
    earth_visible: bool
    optimal_solar: bool
    forecast_note: str


class ForecastResponse(BaseModel):
    crater_id: str
    datetime_utc: str
    source: str
    moon_ecl_lon: float
    sun_ecl_lon: float
    subsolar_lon: float
    subsolar_lat: float
    subearth_lon: float
    subearth_lat: float
    zones: List[ZoneForecast]
    recommended_zone: Optional[str] = None


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.get("", response_model=ForecastResponse)
def get_forecast(
    crater_id: str = Query("tycho", description="tycho | copernicus | clavius"),
    dt: str = Query(..., description="ISO-8601 UTC, e.g. 2027-03-15T12:00:00Z"),
):
    if crater_id not in _CRATERS:
        raise HTTPException(400, f"Unknown crater_id '{crater_id}'. Choose: {list(_CRATERS)}")

    try:
        parsed_dt = datetime.fromisoformat(dt.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        raise HTTPException(400, f"Invalid dt '{dt}'. Expected ISO-8601 UTC.")

    # Import here so the module is optional (Horizons client may fail in offline envs)
    try:
        from data_platform.horizons_client import get_moon_geometry, solar_elev_deg, earth_elev_deg
    except ImportError:
        from data_platform.horizons_client import get_moon_geometry, solar_elev_deg, earth_elev_deg  # noqa: F811

    try:
        # Run the two sequential HTTP calls in a thread (they are sync)
        geom = asyncio.get_event_loop().run_in_executor(None, get_moon_geometry, parsed_dt)
        # For a sync endpoint FastAPI will run this in a thread pool already;
        # get_moon_geometry is sync so direct call is fine here.
        geom = get_moon_geometry(parsed_dt)
    except Exception as exc:
        raise HTTPException(502, f"JPL Horizons fetch failed: {exc}")

    crater = _CRATERS[crater_id]
    zone_forecasts: list[ZoneForecast] = []
    best_zone: Optional[str] = None
    best_score = -999.0

    for fx in _FIXTURES:
        lat, lon = _zone_lat_lon(crater, fx)
        sol = round(solar_elev_deg(lat, lon, geom), 1)
        ear = round(earth_elev_deg(lat, lon, geom), 1)
        lit = sol > 0
        vis = ear > 0
        optimal = 10.0 <= sol <= 45.0

        if lit and vis:
            note = "İDEAL — aydınlık & iletişim açık"
        elif lit and not vis:
            note = "KARIŞIK — aydınlık ama Dünya görünmüyor"
        elif not lit and vis:
            note = "RİSKLİ — Dünya görünür ama bölge karanlık"
        else:
            note = "ELVERİŞSİZ — karanlık & iletişim yok"

        composite = sol * 0.6 + ear * 0.4
        if composite > best_score:
            best_score = composite
            best_zone = fx["id"]

        zone_forecasts.append(ZoneForecast(
            zone_id=fx["id"],
            lat=round(lat, 4),
            lon=round(lon, 4),
            solar_elevation_deg=sol,
            earth_elevation_deg=ear,
            solar_lit=lit,
            earth_visible=vis,
            optimal_solar=optimal,
            forecast_note=note,
        ))

    return ForecastResponse(
        crater_id=crater_id,
        datetime_utc=geom["datetime_utc"],
        source=geom["source"],
        moon_ecl_lon=geom["moon_ecl_lon"],
        sun_ecl_lon=geom["sun_ecl_lon"],
        subsolar_lon=geom["subsolar_lon"],
        subsolar_lat=geom["subsolar_lat"],
        subearth_lon=geom["subearth_lon"],
        subearth_lat=geom["subearth_lat"],
        zones=zone_forecasts,
        recommended_zone=best_zone,
    )
