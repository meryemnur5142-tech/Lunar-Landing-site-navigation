"""
Efficiency windows route — POST /efficiency-windows

Given a landing site candidate ID (or inline candidate data), returns four
orbital landing windows with computed efficiency percentages and conditions.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from luna_ai.sample_data import CANDIDATES
from mission_intelligence.efficiency.landing_efficiency import (
    EfficiencyCalculator,
    LandingWindow,
)

router = APIRouter(prefix="/efficiency", tags=["efficiency"])

_CALC = EfficiencyCalculator()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EfficiencyWindowResponse(BaseModel):
    window_id: str
    label: str
    utc_time: str
    solar_elevation_deg: float
    earth_elevation_deg: float
    descent_angle_deg: float
    delta_v_penalty_ms: float
    solar_flux_wm2: float
    link_margin_dbm: float
    comm_mode: str
    efficiency_pct: float
    terrain_score: float
    window_quality: float
    dominant_factor: str
    conditions: dict


class EfficiencyWindowsResponse(BaseModel):
    candidate_id: str
    crater_name: Optional[str]
    center_lat: float
    center_lon: float
    diameter_km: float
    max_slope_deg: float
    psr_access_fraction: float
    rock_abundance: float
    windows: List[EfficiencyWindowResponse]
    recommended_window_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/craters")
def list_craters():
    """List all candidate craters available for efficiency analysis."""
    return [
        {
            "candidate_id": c.candidate_id,
            "crater_name": c.crater.name,
            "center_lat": c.crater.center_lat,
            "center_lon": c.crater.center_lon,
            "diameter_km": c.crater.diameter_km,
            "max_slope_deg": c.max_slope_deg,
            "psr_access_fraction": c.psr_access_fraction,
            "rock_abundance": c.rock_abundance,
        }
        for c in CANDIDATES
    ]


@router.get("/windows/{candidate_id}", response_model=EfficiencyWindowsResponse)
def get_efficiency_windows(candidate_id: str):
    """Compute four landing efficiency windows for the given candidate.

    Returns efficiency percentages, orbital conditions, and a recommendation
    for each of the four pre-computed orbital windows.
    """
    candidate = next(
        (c for c in CANDIDATES if c.candidate_id == candidate_id), None
    )
    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate '{candidate_id}' not found. "
                   f"Use GET /efficiency/craters to list available candidates.",
        )

    windows: List[LandingWindow] = _CALC.compute_windows(candidate)
    best = max(windows, key=lambda w: w.efficiency_pct)

    return EfficiencyWindowsResponse(
        candidate_id=candidate.candidate_id,
        crater_name=candidate.crater.name,
        center_lat=candidate.crater.center_lat,
        center_lon=candidate.crater.center_lon,
        diameter_km=candidate.crater.diameter_km,
        max_slope_deg=candidate.max_slope_deg,
        psr_access_fraction=candidate.psr_access_fraction,
        rock_abundance=candidate.rock_abundance,
        windows=[
            EfficiencyWindowResponse(
                window_id=w.window_id,
                label=w.label,
                utc_time=w.utc_time,
                solar_elevation_deg=w.solar_elevation_deg,
                earth_elevation_deg=w.earth_elevation_deg,
                descent_angle_deg=w.descent_angle_deg,
                delta_v_penalty_ms=w.delta_v_penalty_ms,
                solar_flux_wm2=w.solar_flux_wm2,
                link_margin_dbm=w.link_margin_dbm,
                comm_mode=w.comm_mode,
                efficiency_pct=w.efficiency_pct,
                terrain_score=w.terrain_score,
                window_quality=w.window_quality,
                dominant_factor=w.dominant_factor,
                conditions=w.conditions,
            )
            for w in windows
        ],
        recommended_window_id=best.window_id,
    )
