"""
Sensitivity analysis route — POST /efficiency/sensitivity

Given a candidate ID and optional parameter overrides, computes landing
efficiency windows under the modified conditions and returns the results
alongside a per-window delta compared to the unmodified baseline.

Terrain overrides (max_slope_deg, rock_abundance, psr_access_fraction) are
applied by creating a copy of the LandingSiteCandidate via dataclasses.replace.
Orbital overrides (solar_elevation_deg, earth_elevation_deg, descent_angle_deg,
delta_v_penalty_ms) are applied by deep-copying _ORBITAL_CONFIGS and patching
the relevant keys across all four windows, then injecting the modified list
into a fresh EfficiencyCalculator instance.
"""

from __future__ import annotations

import copy
import dataclasses
from typing import List

from fastapi import APIRouter, HTTPException

from luna_ai.sample_data import CANDIDATES
from mission_intelligence.efficiency.landing_efficiency import (
    EfficiencyCalculator,
    LandingWindow,
    _ORBITAL_CONFIGS,
)
from ..schemas import (
    LandingWindowOut,
    SensitivityOverrides,
    SensitivityRequest,
    SensitivityResponse,
)

router = APIRouter(prefix="/efficiency", tags=["efficiency"])

# Factor weights match _combined_efficiency in landing_efficiency.py
_FACTOR_WEIGHTS = {"terrain": 0.35, "science": 0.25, "window": 0.40}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _window_to_out(w: LandingWindow) -> LandingWindowOut:
    return LandingWindowOut(
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


def _apply_overrides(candidate, overrides: SensitivityOverrides):
    """Return (overridden_candidate, overridden_orbital_configs).

    terrain overrides  -> dataclasses.replace on the candidate copy
    orbital overrides  -> deep copy of _ORBITAL_CONFIGS with patched values
    """
    # --- terrain ---
    terrain_kwargs = {}
    if overrides.max_slope_deg is not None:
        terrain_kwargs["max_slope_deg"] = overrides.max_slope_deg
    if overrides.psr_access_fraction is not None:
        terrain_kwargs["psr_access_fraction"] = overrides.psr_access_fraction
    if overrides.rock_abundance is not None:
        terrain_kwargs["rock_abundance"] = overrides.rock_abundance

    overridden_candidate = (
        dataclasses.replace(candidate, **terrain_kwargs)
        if terrain_kwargs
        else candidate
    )

    # --- orbital ---
    _ORBITAL_KEY_MAP = {
        "solar_elevation_deg": "solar_deg",
        "earth_elevation_deg": "earth_deg",
        "descent_angle_deg": "descent_angle_deg",
        "delta_v_penalty_ms": "delta_v_penalty_ms",
    }
    orbital_patch = {}
    for attr, cfg_key in _ORBITAL_KEY_MAP.items():
        val = getattr(overrides, attr)
        if val is not None:
            orbital_patch[cfg_key] = val

    if orbital_patch:
        new_configs = [{**cfg, **orbital_patch} for cfg in _ORBITAL_CONFIGS]
    else:
        new_configs = None  # signal to use the default

    return overridden_candidate, new_configs


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/sensitivity", response_model=SensitivityResponse)
def sensitivity_analysis(body: SensitivityRequest):
    """Compute sensitivity analysis for a landing site candidate.

    Applies optional parameter overrides and returns efficiency windows plus
    per-window deltas compared to the unmodified baseline.
    """
    candidate = next(
        (c for c in CANDIDATES if c.candidate_id == body.candidate_id), None
    )
    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Candidate '{body.candidate_id}' not found. "
                "Use GET /efficiency/craters to list available candidates."
            ),
        )

    # Baseline (unmodified)
    baseline_calc = EfficiencyCalculator()
    baseline_windows: List[LandingWindow] = baseline_calc.compute_windows(candidate)
    baseline_by_id = {w.window_id: w.efficiency_pct for w in baseline_windows}

    # Override
    overridden_candidate, new_configs = _apply_overrides(candidate, body.overrides)
    override_calc = EfficiencyCalculator(orbital_configs=new_configs)
    override_windows: List[LandingWindow] = override_calc.compute_windows(
        overridden_candidate
    )

    best = max(override_windows, key=lambda w: w.efficiency_pct)

    delta_vs_baseline = {
        w.window_id: round(w.efficiency_pct - baseline_by_id[w.window_id], 2)
        for w in override_windows
    }

    return SensitivityResponse(
        candidate_id=candidate.candidate_id,
        crater_name=candidate.crater.name,
        windows=[_window_to_out(w) for w in override_windows],
        recommended_window_id=best.window_id,
        factor_weights=_FACTOR_WEIGHTS,
        delta_vs_baseline=delta_vs_baseline,
    )
