"""
Unit tests for LUNA-AI domain models.

Tests cover:
- ScoringWeights validation (must sum to 1.0).
- HardConstraintEvaluator pass/fail behaviour.
- DataProductMetadata required field validation.
- LandingSiteCandidate construction and field constraints.
- BoundingBox construction.
- CraterRecord construction.

Run with:
    pytest tests/unit/test_models.py -v
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from domain.crater.models import (
    CraterRecord,
    DataProductMetadata,
    LandingSiteCandidate,
    RankedCandidate,
)
from domain.environment.models import BoundingBox, EnvironmentalDataProduct, PSRBoundary
from domain.mission.models import HardConstraint, MissionObjective, ScoringWeights
from mission_intelligence.constraints.hard_constraints import HardConstraintEvaluator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime(2027, 1, 1, tzinfo=timezone.utc)


def _metadata(quality: float = 1.0, uncertainty: float | None = None) -> DataProductMetadata:
    return DataProductMetadata(
        source="TEST",
        timestamp=_utc_now(),
        coordinate_reference_system="IAU_MOON_2015",
        resolution_m=20.0,
        quality_score=quality,
        processing_version="0.1.0",
        uncertainty_1sigma=uncertainty,
    )


def _crater(crater_id: str = "TEST-001") -> CraterRecord:
    return CraterRecord(
        crater_id=crater_id,
        center_lat=-85.0,
        center_lon=0.0,
        diameter_km=20.0,
        source_catalog="Robbins2019",
        metadata=_metadata(),
    )


def _candidate(
    candidate_id: str = "CAND-001",
    max_slope_deg: float = 10.0,
    roughness_rms_m: float = 0.3,
    rock_abundance: float = 0.10,
    psr_access_fraction: float = 0.20,
) -> LandingSiteCandidate:
    return LandingSiteCandidate(
        candidate_id=candidate_id,
        crater=_crater(),
        landing_ellipse_center_lat=-85.0,
        landing_ellipse_center_lon=0.0,
        landing_ellipse_semi_major_m=500.0,
        landing_ellipse_semi_minor_m=250.0,
        max_slope_deg=max_slope_deg,
        roughness_rms_m=roughness_rms_m,
        rock_abundance=rock_abundance,
        psr_access_fraction=psr_access_fraction,
        metadata=_metadata(),
    )


# ---------------------------------------------------------------------------
# DataProductMetadata tests
# ---------------------------------------------------------------------------


class TestDataProductMetadata:
    def test_valid_construction(self) -> None:
        meta = _metadata(quality=0.85)
        assert meta.quality_score == 0.85
        assert meta.coordinate_reference_system == "IAU_MOON_2015"

    def test_quality_score_too_high_raises(self) -> None:
        with pytest.raises(ValueError, match="quality_score"):
            DataProductMetadata(
                source="TEST",
                timestamp=_utc_now(),
                coordinate_reference_system="IAU_MOON_2015",
                resolution_m=20.0,
                quality_score=1.1,
                processing_version="0.1.0",
            )

    def test_quality_score_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="quality_score"):
            DataProductMetadata(
                source="TEST",
                timestamp=_utc_now(),
                coordinate_reference_system="IAU_MOON_2015",
                resolution_m=20.0,
                quality_score=-0.1,
                processing_version="0.1.0",
            )

    def test_zero_resolution_raises(self) -> None:
        with pytest.raises(ValueError, match="resolution_m"):
            DataProductMetadata(
                source="TEST",
                timestamp=_utc_now(),
                coordinate_reference_system="IAU_MOON_2015",
                resolution_m=0.0,
                quality_score=0.9,
                processing_version="0.1.0",
            )

    def test_optional_fields_default_to_none(self) -> None:
        meta = _metadata()
        assert meta.uncertainty_1sigma is None
        assert meta.lineage == []


# ---------------------------------------------------------------------------
# CraterRecord tests
# ---------------------------------------------------------------------------


class TestCraterRecord:
    def test_valid_construction(self) -> None:
        crater = _crater()
        assert crater.crater_id == "TEST-001"
        assert crater.name is None

    def test_named_crater(self) -> None:
        crater = CraterRecord(
            crater_id="R-00042",
            name="Shackleton",
            center_lat=-89.9,
            center_lon=0.0,
            diameter_km=21.0,
            source_catalog="Robbins2019",
            metadata=_metadata(),
        )
        assert crater.name == "Shackleton"

    def test_lat_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="center_lat"):
            CraterRecord(
                crater_id="BAD",
                center_lat=91.0,
                center_lon=0.0,
                diameter_km=5.0,
                source_catalog="TEST",
                metadata=_metadata(),
            )

    def test_negative_diameter_raises(self) -> None:
        with pytest.raises(ValueError, match="diameter_km"):
            CraterRecord(
                crater_id="BAD",
                center_lat=-85.0,
                center_lon=0.0,
                diameter_km=-1.0,
                source_catalog="TEST",
                metadata=_metadata(),
            )


# ---------------------------------------------------------------------------
# LandingSiteCandidate tests
# ---------------------------------------------------------------------------


class TestLandingSiteCandidate:
    def test_valid_construction(self) -> None:
        cand = _candidate()
        assert cand.candidate_id == "CAND-001"
        assert cand.hard_constraints_passed is None
        assert cand.rejection_reason is None

    def test_rock_abundance_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="rock_abundance"):
            _candidate(rock_abundance=1.5)

    def test_psr_access_fraction_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="psr_access_fraction"):
            _candidate(psr_access_fraction=-0.1)

    def test_negative_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="max_slope_deg"):
            _candidate(max_slope_deg=-5.0)


# ---------------------------------------------------------------------------
# ScoringWeights tests
# ---------------------------------------------------------------------------


class TestScoringWeights:
    def test_default_weights_sum_to_one(self) -> None:
        w = ScoringWeights()
        total = w.science + w.energy + w.thermal + w.communication + w.risk
        assert math.isclose(total, 1.0, abs_tol=1e-9)

    def test_custom_valid_weights(self) -> None:
        w = ScoringWeights(
            science=0.40,
            energy=0.20,
            thermal=0.20,
            communication=0.10,
            risk=0.10,
        )
        assert math.isclose(w.science, 0.40)

    def test_weights_not_summing_to_one_raises(self) -> None:
        with pytest.raises(ValueError, match="sum to 1.0"):
            ScoringWeights(
                science=0.40,
                energy=0.30,
                thermal=0.20,
                communication=0.15,
                risk=0.10,
            )

    def test_negative_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            ScoringWeights(
                science=0.40,
                energy=-0.10,
                thermal=0.30,
                communication=0.25,
                risk=0.15,
            )


# ---------------------------------------------------------------------------
# HardConstraintEvaluator tests
# ---------------------------------------------------------------------------


class TestHardConstraintEvaluator:
    def _evaluator(self) -> HardConstraintEvaluator:
        return HardConstraintEvaluator(HardConstraintEvaluator.default_constraints())

    def test_passing_candidate(self) -> None:
        passed, reason = self._evaluator().evaluate(_candidate())
        assert passed is True
        assert reason is None

    def test_slope_violation_rejected(self) -> None:
        passed, reason = self._evaluator().evaluate(_candidate(max_slope_deg=20.0))
        assert passed is False
        assert reason is not None
        assert "HC-001" in reason

    def test_psr_access_violation_rejected(self) -> None:
        passed, reason = self._evaluator().evaluate(_candidate(psr_access_fraction=0.05))
        assert passed is False
        assert "HC-002" in (reason or "")

    def test_rock_abundance_violation_rejected(self) -> None:
        passed, reason = self._evaluator().evaluate(_candidate(rock_abundance=0.25))
        assert passed is False
        assert "HC-003" in (reason or "")

    def test_batch_filters_correctly(self) -> None:
        evaluator = self._evaluator()
        good = _candidate("GOOD")
        bad = _candidate("BAD", max_slope_deg=20.0)
        result = evaluator.evaluate_batch([good, bad])
        assert len(result) == 1
        assert result[0].candidate_id == "GOOD"
        assert good.hard_constraints_passed is True
        assert bad.hard_constraints_passed is False

    def test_empty_constraints_raises(self) -> None:
        with pytest.raises(ValueError):
            HardConstraintEvaluator([])

    def test_all_constraints_checked_sequentially(self) -> None:
        # First failing constraint determines rejection_reason
        evaluator = self._evaluator()
        bad = _candidate(max_slope_deg=20.0, psr_access_fraction=0.05)
        _, reason = evaluator.evaluate(bad)
        # HC-001 (slope) comes first in default_constraints
        assert "HC-001" in (reason or "")


# ---------------------------------------------------------------------------
# BoundingBox tests
# ---------------------------------------------------------------------------


class TestBoundingBox:
    def test_valid_construction(self) -> None:
        bbox = BoundingBox(min_lat=-86.0, max_lat=-84.0, min_lon=350.0, max_lon=360.0)
        assert math.isclose(bbox.center_lat, -85.0)

    def test_inverted_lat_raises(self) -> None:
        with pytest.raises(ValueError, match="min_lat"):
            BoundingBox(min_lat=-84.0, max_lat=-86.0, min_lon=350.0, max_lon=360.0)

    def test_inverted_lon_raises(self) -> None:
        with pytest.raises(ValueError, match="min_lon"):
            BoundingBox(min_lat=-86.0, max_lat=-84.0, min_lon=360.0, max_lon=350.0)


# ---------------------------------------------------------------------------
# RankedCandidate tests
# ---------------------------------------------------------------------------


class TestRankedCandidate:
    def test_valid_construction(self) -> None:
        cand = _candidate()
        cand.hard_constraints_passed = True
        ranked = RankedCandidate(
            candidate=cand,
            science_score=0.8,
            energy_score=0.7,
            thermal_score=0.6,
            communication_score=0.5,
            risk_score=0.9,
            total_score=0.72,
            score_uncertainty=0.12,
        )
        assert ranked.total_score == 0.72

    def test_score_out_of_range_raises(self) -> None:
        cand = _candidate()
        with pytest.raises(ValueError):
            RankedCandidate(
                candidate=cand,
                science_score=1.5,  # out of range
                energy_score=0.7,
                thermal_score=0.6,
                communication_score=0.5,
                risk_score=0.9,
                total_score=0.72,
                score_uncertainty=0.12,
            )
