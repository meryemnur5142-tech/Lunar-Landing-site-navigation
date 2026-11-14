"""
Integration tests: HardConstraintEvaluator → CandidateScorer pipeline.

Tests verify that the two-stage safety gate (HC evaluation, then scoring)
behaves correctly end-to-end using the real domain models and default
constraint/weight configurations.

Run with:
    pytest tests/integration/test_pipeline.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from domain.crater.models import CraterRecord, DataProductMetadata, LandingSiteCandidate
from domain.environment.models import EnvironmentalDataProduct
from domain.mission.models import MissionObjective, ScoringWeights
from mission_intelligence.constraints.hard_constraints import HardConstraintEvaluator
from mission_intelligence.scoring.scorer import CandidateScorer


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_UTC = timezone.utc


def _meta(quality: float = 1.0) -> DataProductMetadata:
    return DataProductMetadata(
        source="TEST",
        timestamp=datetime(2027, 1, 1, tzinfo=_UTC),
        coordinate_reference_system="IAU_MOON_2015",
        resolution_m=20.0,
        quality_score=quality,
        processing_version="0.1.0",
    )


def _crater(crater_id: str = "CRT-001") -> CraterRecord:
    return CraterRecord(
        crater_id=crater_id,
        center_lat=-85.0,
        center_lon=0.0,
        diameter_km=20.0,
        source_catalog="TEST",
        metadata=_meta(),
    )


def _candidate(
    candidate_id: str = "CAND-001",
    max_slope_deg: float = 10.0,
    psr_access_fraction: float = 0.25,
    rock_abundance: float = 0.10,
    roughness_rms_m: float = 0.3,
) -> LandingSiteCandidate:
    """Build a minimal LandingSiteCandidate for integration testing."""
    return LandingSiteCandidate(
        candidate_id=candidate_id,
        crater=_crater(crater_id=f"CRT-{candidate_id}"),
        landing_ellipse_center_lat=-85.0,
        landing_ellipse_center_lon=0.0,
        landing_ellipse_semi_major_m=500.0,
        landing_ellipse_semi_minor_m=250.0,
        max_slope_deg=max_slope_deg,
        roughness_rms_m=roughness_rms_m,
        rock_abundance=rock_abundance,
        psr_access_fraction=psr_access_fraction,
        metadata=_meta(),
    )


def _default_objectives() -> List[MissionObjective]:
    return [
        MissionObjective(
            objective_id="OBJ-001",
            description="Characterise PSR volatile deposits",
            priority=1,
            science_category="volatiles",
            minimum_psr_access_hours=4.0,
        )
    ]


def _make_scorer() -> CandidateScorer:
    return CandidateScorer(
        weights=ScoringWeights(),
        mission_objectives=_default_objectives(),
    )


def _make_evaluator() -> HardConstraintEvaluator:
    return HardConstraintEvaluator(HardConstraintEvaluator.default_constraints())


# ---------------------------------------------------------------------------
# Test 1: When all candidates pass HC, the ranked list is fully populated
# ---------------------------------------------------------------------------


def test_all_pass_hc_produces_ranked_list() -> None:
    """When every candidate satisfies all hard constraints, rank() returns
    one RankedCandidate per input candidate, sorted by total_score descending."""
    evaluator = _make_evaluator()
    scorer = _make_scorer()

    candidates = [
        _candidate("CAND-A", max_slope_deg=5.0, psr_access_fraction=0.40),
        _candidate("CAND-B", max_slope_deg=12.0, psr_access_fraction=0.15),
    ]

    passing = evaluator.evaluate_batch(candidates)
    assert len(passing) == 2, "Both candidates must pass HC"

    ranked = scorer.rank(passing, env_products={})
    assert len(ranked) == 2

    # Results must be sorted in descending order
    assert ranked[0].total_score >= ranked[1].total_score

    # Every score must lie in [0, 1]
    for rc in ranked:
        assert 0.0 <= rc.total_score <= 1.0
        assert 0.0 <= rc.score_uncertainty <= 1.0


# ---------------------------------------------------------------------------
# Test 2: Candidates that fail HC are excluded from the ranked list
# ---------------------------------------------------------------------------


def test_failed_hc_candidates_excluded_from_ranking() -> None:
    """Candidates that fail any hard constraint must not appear in rank()
    output — the safety gate must be watertight end-to-end."""
    evaluator = _make_evaluator()
    scorer = _make_scorer()

    good = _candidate("CAND-GOOD", max_slope_deg=8.0, psr_access_fraction=0.30)
    bad_slope = _candidate("CAND-BAD-SLOPE", max_slope_deg=20.0)   # HC-001 fail
    bad_psr = _candidate("CAND-BAD-PSR", psr_access_fraction=0.05)  # HC-002 fail

    all_candidates = [good, bad_slope, bad_psr]
    passing = evaluator.evaluate_batch(all_candidates)

    # Only the good candidate must pass
    assert len(passing) == 1
    assert passing[0].candidate_id == "CAND-GOOD"

    # Failed candidates must be annotated
    assert bad_slope.hard_constraints_passed is False
    assert bad_psr.hard_constraints_passed is False
    assert "HC-001" in (bad_slope.rejection_reason or "")
    assert "HC-002" in (bad_psr.rejection_reason or "")

    # Only the passing candidate must be ranked
    ranked = scorer.rank(all_candidates, env_products={})
    ranked_ids = {rc.candidate.candidate_id for rc in ranked}
    assert "CAND-GOOD" in ranked_ids
    assert "CAND-BAD-SLOPE" not in ranked_ids
    assert "CAND-BAD-PSR" not in ranked_ids


# ---------------------------------------------------------------------------
# Test 3: Candidate with higher PSR access fraction achieves a better science score
# ---------------------------------------------------------------------------


def test_higher_psr_candidate_scores_better_science() -> None:
    """A candidate with higher PSR access fraction must receive a higher
    science score than an otherwise identical candidate with lower PSR access.

    This verifies the science_score component responds monotonically to
    psr_access_fraction when both candidates pass hard constraints."""
    evaluator = _make_evaluator()
    scorer = _make_scorer()

    low_psr = _candidate("LOW-PSR", psr_access_fraction=0.15)
    high_psr = _candidate("HIGH-PSR", psr_access_fraction=0.60)

    passing = evaluator.evaluate_batch([low_psr, high_psr])
    assert len(passing) == 2

    env: dict = {}
    ranked = scorer.rank(passing, env_products=env)
    assert len(ranked) == 2

    scores = {rc.candidate.candidate_id: rc for rc in ranked}
    assert scores["HIGH-PSR"].science_score > scores["LOW-PSR"].science_score, (
        "Higher PSR access fraction must raise the science score"
    )
    # Note: thermal_score is inversely proportional to PSR access (thermal = 1 - psr_fraction).
    # Therefore overall ranking does not necessarily align with PSR access fraction;
    # the purpose of this test is to verify science_score monotonicity.
