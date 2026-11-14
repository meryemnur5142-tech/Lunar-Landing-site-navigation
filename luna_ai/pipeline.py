"""End-to-end candidate evaluation pipeline: HC filter → score → rank."""

from __future__ import annotations

from dataclasses import dataclass

from domain.crater.models import LandingSiteCandidate, RankedCandidate
from domain.environment.models import EnvironmentalDataProduct
from domain.mission.models import MissionObjective, ScoringWeights
from mission_intelligence.constraints.hard_constraints import HardConstraintEvaluator
from mission_intelligence.scoring.scorer import CandidateScorer

# Default mission objectives for the demo (south-pole PSR volatile characterisation)
_DEFAULT_OBJECTIVES = [
    MissionObjective(
        objective_id="OBJ-001",
        description="Characterise PSR volatile deposits in south-pole region",
        priority=1,
        science_category="volatiles",
        minimum_psr_access_hours=4.0,
    ),
    MissionObjective(
        objective_id="OBJ-002",
        description="Assess water-ice resource potential for ISRU",
        priority=2,
        science_category="resource_assessment",
        minimum_psr_access_hours=2.0,
    ),
]

_DEFAULT_WEIGHTS = ScoringWeights(
    science=0.35,
    energy=0.25,
    thermal=0.15,
    communication=0.10,
    risk=0.15,
)


@dataclass
class PipelineResult:
    total_candidates: int
    passed_hc: int
    rejected_hc: int
    ranked: list[RankedCandidate]
    rejection_summary: list[tuple[str, str]]  # (candidate_id, reason)


def run_pipeline(
    candidates: list[LandingSiteCandidate],
    weights: ScoringWeights | None = None,
    objectives: list[MissionObjective] | None = None,
    env_products: dict[str, EnvironmentalDataProduct] | None = None,
) -> PipelineResult:
    """Filter candidates through hard constraints, then score and rank survivors.

    Args:
        candidates: Unevaluated landing site candidates.
        weights: Scoring dimension weights (defaults to science-biased preset).
        objectives: Mission science objectives used to calibrate science score.
        env_products: Optional environmental data per candidate_id; missing
                      entries use an empty EnvironmentalDataProduct.
    """
    if weights is None:
        weights = _DEFAULT_WEIGHTS
    if objectives is None:
        objectives = _DEFAULT_OBJECTIVES
    if env_products is None:
        env_products = {}

    evaluator = HardConstraintEvaluator(HardConstraintEvaluator.default_constraints())
    scorer = CandidateScorer(weights, objectives)

    passed = evaluator.evaluate_batch(candidates)

    rejection_summary = [
        (c.candidate_id, c.rejection_reason or "unknown")
        for c in candidates
        if not c.hard_constraints_passed
    ]

    ranked = scorer.rank(passed, env_products)

    return PipelineResult(
        total_candidates=len(candidates),
        passed_hc=len(passed),
        rejected_hc=len(candidates) - len(passed),
        ranked=ranked,
        rejection_summary=rejection_summary,
    )
