"""
/api/v1/candidates  — Run the demo pipeline and return ranked candidates.
/api/v1/constraints — List active hard constraints.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..schemas import (
    ConstraintResponse,
    EvaluateResponse,
    RankedCandidateResponse,
    RejectedCandidate,
)
from luna_ai.pipeline import run_pipeline
from luna_ai.sample_data import CANDIDATES
from mission_intelligence.constraints.hard_constraints import HardConstraintEvaluator

router = APIRouter(prefix="/api/v1", tags=["Candidates"])


@router.get("/candidates", response_model=EvaluateResponse)
def list_candidates():
    """Run the evaluation pipeline on the built-in estimated candidates."""
    return _run_and_format(run_pipeline(CANDIDATES))


@router.get("/constraints", response_model=list[ConstraintResponse])
def list_constraints():
    """Return the active hard constraint definitions."""
    result = []
    for hc in HardConstraintEvaluator.default_constraints():
        # Parse threshold and operator from the constraint's check logic.
        # This is a best-effort representation for the UI.
        result.append(
            ConstraintResponse(
                constraint_id=hc.constraint_id,
                name=hc.name,
                description=hc.description,
                threshold=hc.threshold,
                unit=hc.unit,
                operator=hc.operator,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_and_format(result) -> EvaluateResponse:
    ranked = []
    for i, rc in enumerate(result.ranked, start=1):
        c = rc.candidate
        ranked.append(
            RankedCandidateResponse(
                rank=i,
                candidate_id=c.candidate_id,
                crater_name=c.crater.name,
                total_score=round(rc.total_score, 4),
                score_uncertainty=round(rc.score_uncertainty, 4),
                science_score=round(rc.science_score, 4),
                energy_score=round(rc.energy_score, 4),
                thermal_score=round(rc.thermal_score, 4),
                communication_score=round(rc.communication_score, 4),
                risk_score=round(rc.risk_score, 4),
                max_slope_deg=c.max_slope_deg,
                psr_access_fraction=c.psr_access_fraction,
                rock_abundance=c.rock_abundance,
            )
        )

    rejected = [
        RejectedCandidate(candidate_id=cid, reason=reason)
        for cid, reason in result.rejection_summary
    ]

    recommendation = result.ranked[0].candidate.candidate_id if result.ranked else None

    return EvaluateResponse(
        total_candidates=result.total_candidates,
        passed_hc=result.passed_hc,
        rejected_hc=result.rejected_hc,
        rejected=rejected,
        ranked=ranked,
        recommendation=recommendation,
    )
