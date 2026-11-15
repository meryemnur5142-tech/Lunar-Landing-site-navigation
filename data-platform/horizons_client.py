"""
NASA JPL Horizons API client — lunar surface geometry for landing forecasts.

API reference: https://ssd-api.jpl.nasa.gov/doc/horizons.html

Fetches:
  - Moon's ecliptic longitude/latitude (Observer table, QUANTITIES='31')
  - Sun's ecliptic longitude/latitude (same)
  Then derives:
  - Subsolar selenographic longitude/latitude  (where Sun is overhead on Moon)
  - Sub-Earth selenographic point             (where Earth is overhead on Moon)

Usage:
    from data_platform.horizons_client import get_moon_geometry, solar_elev_deg

    geom = get_moon_geometry(datetime(2027, 3, 15, 12, 0, tzinfo=timezone.utc))
    print(geom)
    # {'subsolar_lon': -42.3, 'subsolar_lat': 1.1, ...}

    elev = solar_elev_deg(lat=-43.3, lon=-11.0, geom=geom)
    print(f"Solar elevation: {elev:.1f}°")
"""

from __future__ import annotations

import json
import math
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import TypedDict


HORIZONS_URL = "https://ssd-api.jpl.nasa.gov/horizons.api"
TIMEOUT_S = 15


class MoonGeometry(TypedDict):
    subsolar_lon: float    # selenographic longitude of sub-solar point (deg)
    subsolar_lat: float    # selenographic latitude of sub-solar point (deg)
    subearth_lon: float    # selenographic longitude of sub-Earth point (deg)
    subearth_lat: float    # selenographic latitude of sub-Earth point (deg)
    moon_ecl_lon: float    # Moon's J2000 ecliptic longitude (deg)
    sun_ecl_lon: float     # Sun's J2000 ecliptic longitude (deg)
    datetime_utc: str
    source: str


def _fmt(dt: datetime) -> str:
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%b-%d %H:%M")


def _query_ecl_lon(command: str, dt: datetime) -> dict[str, float]:
    """Return J2000 ecliptic lon/lat for a Horizons body at a given UTC datetime."""
    start = _fmt(dt)
    # stop = start + 1 hour (Horizons requires stop > start)
    h = dt.hour
    stop_dt = dt.replace(hour=(h + 1) % 24)
    if stop_dt <= dt:  # midnight rollover
        stop_dt = dt.replace(day=dt.day + 1, hour=0)
    stop = _fmt(stop_dt)

    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "NO",
        "MAKE_EPHEM": "YES",
        "TABLE_TYPE": "OBSERVER",
        "CENTER": "'500@399'",   # Earth geocenter
        "START_TIME": f"'{start}'",
        "STOP_TIME": f"'{stop}'",
        "STEP_SIZE": "'1h'",
        "QUANTITIES": "'31'",    # ObsEcLon, ObsEcLat (decimal degrees)
    }
    url = HORIZONS_URL + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": "LUNA-AI/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        data = json.loads(resp.read())

    if "error" in data:
        raise RuntimeError(f"Horizons error: {data['error']}")

    text: str = data.get("result", "")
    soe = text.find("$$SOE")
    eoe = text.find("$$EOE")
    if soe < 0 or eoe < 0:
        raise ValueError("Horizons ephemeris block not found in response")

    # First non-empty data line after $$SOE
    data_line = next(
        (ln for ln in text[soe + 6:eoe].splitlines() if ln.strip()),
        None,
    )
    if not data_line:
        raise ValueError("No data line found in Horizons ephemeris block")

    # Extract floating-point numbers (date/time fields have no decimal point)
    import re
    nums = [float(m) for m in re.findall(r"[+-]?\d+\.\d+", data_line)]
    if len(nums) < 2:
        raise ValueError(f"Could not parse ecliptic lon/lat from: {data_line!r}")

    return {"lon": nums[0], "lat": nums[1]}


def get_moon_geometry(dt: datetime) -> MoonGeometry:
    """
    Fetch Moon geometry from JPL Horizons for a given datetime.

    Both queries run sequentially (not async). Call from a thread pool
    when used inside an async FastAPI endpoint.

    Raises RuntimeError / ValueError on network or parse failure.
    """
    moon = _query_ecl_lon("301", dt)   # Moon
    sun  = _query_ecl_lon("10",  dt)   # Sun

    # Sub-solar selenographic longitude
    # Moon is tidally locked: near-side center (sel.lon=0°) ≈ faces Earth.
    # Sub-solar lon = (Sun_ecl_lon - Moon_ecl_lon), wrapped to -180..+180
    d_lon = ((sun["lon"] - moon["lon"]) % 360 + 360) % 360
    if d_lon > 180:
        d_lon -= 360
    subsolar_lon = d_lon
    # Subsolar lat ≈ differential ecliptic latitude (Moon's axial tilt is 1.54°)
    subsolar_lat = float(sun["lat"] - moon["lat"])
    subsolar_lat = max(-10.0, min(10.0, subsolar_lat))

    # Sub-Earth point: Moon's tidal lock keeps near-side ≈ facing Earth.
    # True libration is ±7.9° lon / ±6.9° lat (omitted in this demo).
    return MoonGeometry(
        subsolar_lon=round(subsolar_lon, 2),
        subsolar_lat=round(subsolar_lat, 2),
        subearth_lon=0.0,
        subearth_lat=0.0,
        moon_ecl_lon=round(moon["lon"], 2),
        sun_ecl_lon=round(sun["lon"], 2),
        datetime_utc=_fmt(dt),
        source="JPL Horizons",
    )


def _ang_sep(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Angular separation → elevation of point2 as seen from point1 on a sphere."""
    r = math.radians
    cos_z = (
        math.sin(r(lat1)) * math.sin(r(lat2))
        + math.cos(r(lat1)) * math.cos(r(lat2)) * math.cos(r(lon1 - lon2))
    )
    return math.degrees(math.asin(max(-1.0, min(1.0, cos_z))))


def solar_elev_deg(lat: float, lon: float, geom: MoonGeometry) -> float:
    """Solar elevation (degrees) at a lunar surface point. Positive = Sun above horizon."""
    return _ang_sep(lat, lon, geom["subsolar_lat"], geom["subsolar_lon"])


def earth_elev_deg(lat: float, lon: float, geom: MoonGeometry) -> float:
    """Earth elevation (degrees) at a lunar surface point. Positive = Earth visible."""
    return _ang_sep(lat, lon, geom["subearth_lat"], geom["subearth_lon"])
