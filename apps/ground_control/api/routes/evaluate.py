"""POST /api/v1/evaluate — run pipeline on caller-supplied candidates."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..schemas import EvaluateRequest, EvaluateResponse
from .candidates import _run_and_format, _try_log_run
from domain.crater.models import CraterRecord, DataProductMetadata, LandingSiteCandidate
from domain.mission.models import ScoringWeights
from luna_ai.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Evaluate"])


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_candidates(body: EvaluateRequest):
    """
    Evaluate a caller-supplied list of landing site candidates.

    The pipeline runs hard-constraint filtering followed by weighted
    multi-criteria scoring. Returns ranked survivors and rejection details.
    """
    if not body.candidates:
        raise HTTPException(status_code=422, detail="candidates list must not be empty")

    _meta = DataProductMetadata(
        source="USER_INPUT",
        timestamp=datetime.now(timezone.utc),
        coordinate_reference_system="IAU_MOON_2015",
        resolution_m=20.0,
        quality_score=0.70,
        processing_version="user-input-v1",
    )

    candidates: list[LandingSiteCandidate] = []
    for inp in body.candidates:
        crater = CraterRecord(
            crater_id=f"USR-{inp.candidate_id}",
            name=inp.crater_name,
            center_lat=inp.center_lat,
            center_lon=inp.center_lon,
            diameter_km=inp.diameter_km,
            source_catalog="USER_INPUT",
            metadata=_meta,
        )
        candidates.append(
            LandingSiteCandidate(
                candidate_id=inp.candidate_id,
                crater=crater,
                landing_ellipse_center_lat=inp.center_lat,
                landing_ellipse_center_lon=inp.center_lon,
                landing_ellipse_semi_major_m=500.0,
                landing_ellipse_semi_minor_m=250.0,
                max_slope_deg=inp.max_slope_deg,
                roughness_rms_m=inp.roughness_rms_m,
                rock_abundance=inp.rock_abundance,
                psr_access_fraction=inp.psr_access_fraction,
                metadata=_meta,
            )
        )

    weights = None
    if body.weights:
        weights = ScoringWeights(
            science=body.weights.science,
            energy=body.weights.energy,
            thermal=body.weights.thermal,
            communication=body.weights.communication,
            risk=body.weights.risk,
        )

    result = run_pipeline(candidates, weights=weights)

    weights_dict = {
        "science": body.weights.science if body.weights else 0.35,
        "energy": body.weights.energy if body.weights else 0.25,
        "thermal": body.weights.thermal if body.weights else 0.15,
        "communication": body.weights.communication if body.weights else 0.10,
        "risk": body.weights.risk if body.weights else 0.15,
    }
    _try_log_run(result, mode="user", weights_dict=weights_dict)

    return _run_and_format(result)
