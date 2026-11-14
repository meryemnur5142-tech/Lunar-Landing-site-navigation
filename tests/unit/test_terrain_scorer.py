"""
Unit tests for TerrainAnalyzer and CandidateScorer.

Covers:
- TerrainAnalyzer.compute_slope  (flat terrain → ~0°; ramp → ~45°)
- TerrainAnalyzer.compute_roughness  (uniform surface → 0 m)
- TerrainAnalyzer.compute_hazard_map (zero inputs → ~0; steep slope → >0.5)
- CandidateScorer.rank  (returns RankedCandidate; scores in [0,1]; higher
  illumination raises energy_score; empty env yields non-zero uncertainty)

TerrainAnalyzer lives in ``data-platform/processing/terrain_analyzer.py``.
The directory name contains a hyphen which makes it a non-importable Python
identifier, so we load the module via ``importlib.util.spec_from_file_location``.

Run with:
    pytest tests/unit/test_terrain_scorer.py -v
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Import TerrainAnalyzer through importlib (data-platform dir has a hyphen)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "terrain_analyzer",
    _ROOT / "data-platform" / "processing" / "terrain_analyzer.py",
)
_ta_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_ta_mod)  # type: ignore[union-attr]
TerrainAnalyzer = _ta_mod.TerrainAnalyzer

# Standard package imports — these work because conftest.py added _ROOT to
# sys.path before collection starts.
from domain.crater.models import (  # noqa: E402
    CraterRecord,
    DataProductMetadata,
    LandingSiteCandidate,
    RankedCandidate,
)
from domain.environment.models import (  # noqa: E402
    BoundingBox,
    EnvironmentalDataProduct,
    IlluminationTimeSeries,
    TerrainProduct,
)
from domain.mission.models import MissionObjective, ScoringWeights  # noqa: E402
from mission_intelligence.scoring.scorer import CandidateScorer  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_EXTENT = BoundingBox(min_lat=-86.0, max_lat=-84.0, min_lon=0.0, max_lon=2.0)
_UTC = timezone.utc


def _utc_dt(year: int = 2027) -> datetime:
    return datetime(year, 1, 1, tzinfo=_UTC)


def _meta(
    resolution_m: float = 1.0,
    quality: float = 1.0,
    uncertainty: float | None = None,
) -> DataProductMetadata:
    return DataProductMetadata(
        source="TEST_DEM",
        timestamp=_utc_dt(),
        coordinate_reference_system="IAU_MOON_2015",
        resolution_m=resolution_m,
        quality_score=quality,
        processing_version="0.1.0",
        uncertainty_1sigma=uncertainty,
    )


def _dem(data: np.ndarray, resolution_m: float = 1.0) -> TerrainProduct:
    """Wrap a 2-D array in a TerrainProduct.

    ``slope_map`` is used as the product_type placeholder because
    TerrainProduct.product_type has no "dem" literal; TerrainAnalyzer
    does not gate on this field for slope/roughness computation.
    """
    return TerrainProduct(
        product_id="TEST-DEM",
        product_type="slope_map",
        data=data.astype(np.float32),
        extent=_EXTENT,
        metadata=_meta(resolution_m=resolution_m),
    )


def _crater() -> CraterRecord:
    return CraterRecord(
        crater_id="TC-001",
        center_lat=-85.0,
        center_lon=1.0,
        diameter_km=20.0,
        source_catalog="Robbins2019",
        metadata=_meta(),
    )


def _candidate(
    candidate_id: str = "CAND-T01",
    max_slope_deg: float = 5.0,
    roughness_rms_m: float = 0.1,
    psr_access_fraction: float = 0.20,
    rock_abundance: float = 0.05,
) -> LandingSiteCandidate:
    cand = LandingSiteCandidate(
        candidate_id=candidate_id,
        crater=_crater(),
        landing_ellipse_center_lat=-85.0,
        landing_ellipse_center_lon=1.0,
        landing_ellipse_semi_major_m=500.0,
        landing_ellipse_semi_minor_m=250.0,
        max_slope_deg=max_slope_deg,
        roughness_rms_m=roughness_rms_m,
        rock_abundance=rock_abundance,
        psr_access_fraction=psr_access_fraction,
        metadata=_meta(),
    )
    cand.hard_constraints_passed = True
    return cand


def _scorer() -> CandidateScorer:
    weights = ScoringWeights(
        science=0.30,
        energy=0.25,
        thermal=0.20,
        communication=0.15,
        risk=0.10,
    )
    obj = MissionObjective(
        objective_id="OBJ-001",
        description="PSR volatile characterisation",
        priority=1,
        science_category="volatiles",
        minimum_psr_access_hours=4.0,
    )
    return CandidateScorer(weights=weights, mission_objectives=[obj])


# ---------------------------------------------------------------------------
# TerrainAnalyzer — slope tests
# ---------------------------------------------------------------------------


class TestTerrainAnalyzerSlope:
    def test_slope_calculation_flat_terrain(self) -> None:
        """Zero-elevation DEM → every slope pixel must be ~0 degrees (QAR NAV-001)."""
        analyzer = TerrainAnalyzer()
        flat_dem = _dem(np.zeros((10, 10), dtype=np.float32))
        slope = analyzer.compute_slope(flat_dem)

        assert slope.product_type == "slope_map"
        assert slope.data.shape == (10, 10)
        assert float(slope.data.max()) == pytest.approx(0.0, abs=1e-5)

    def test_slope_calculation_steep_terrain(self) -> None:
        """Ramp DEM where elevation = column index (resolution_m=1) → Horn slope ≈ 45°.

        Horn (1981): dz_dx = 1.0 → slope = arctan(1) = 45°.
        Interior pixels are checked (edges use padding).
        """
        analyzer = TerrainAnalyzer()
        rows, cols = 10, 10
        ramp = np.tile(np.arange(cols, dtype=np.float32), (rows, 1))
        dem = _dem(ramp, resolution_m=1.0)
        slope = analyzer.compute_slope(dem)

        interior = slope.data[1:-1, 1:-1]
        assert float(interior.mean()) == pytest.approx(45.0, abs=1.0)


# ---------------------------------------------------------------------------
# TerrainAnalyzer — roughness test
# ---------------------------------------------------------------------------


class TestTerrainAnalyzerRoughness:
    def test_roughness_calculation_uniform(self) -> None:
        """Uniform-height DEM → all patch residuals = 0 → roughness max = 0 m."""
        analyzer = TerrainAnalyzer()
        uniform_dem = _dem(np.full((10, 10), 100.0, dtype=np.float32))
        roughness = analyzer.compute_roughness(uniform_dem)

        assert roughness.product_type == "roughness_map"
        assert float(roughness.data.max()) == pytest.approx(0.0, abs=1e-5)


# ---------------------------------------------------------------------------
# TerrainAnalyzer — hazard map tests
# ---------------------------------------------------------------------------


class TestTerrainAnalyzerHazardMap:
    """Tests for compute_hazard_map (no rock_map → weights 0.625/0.375)."""

    _SHAPE = (5, 5)

    def _zero_slope_product(self) -> TerrainProduct:
        return TerrainProduct(
            product_id="SLOPE-ZERO",
            product_type="slope_map",
            data=np.zeros(self._SHAPE, dtype=np.float32),
            extent=_EXTENT,
            metadata=_meta(),
        )

    def _zero_roughness_product(self) -> TerrainProduct:
        return TerrainProduct(
            product_id="ROUGH-ZERO",
            product_type="roughness_map",
            data=np.zeros(self._SHAPE, dtype=np.float32),
            extent=_EXTENT,
            metadata=_meta(),
        )

    def test_hazard_map_no_hazard(self) -> None:
        """Zero slope + zero roughness → hazard everywhere ≈ 0.0."""
        analyzer = TerrainAnalyzer()
        hazard = analyzer.compute_hazard_map(
            self._zero_slope_product(), self._zero_roughness_product()
        )

        assert hazard.product_type == "hazard_map"
        assert float(hazard.data.max()) == pytest.approx(0.0, abs=1e-5)

    def test_hazard_map_steep_slope(self) -> None:
        """20° slope, zero roughness → hazard = 0.625 × 1.0 + 0.375 × 0 = 0.625 > 0.5.

        slope_norm = clip(20/15, 0, 1) = 1.0
        hazard (no rock_map) = 0.625 × slope_norm + 0.375 × rough_norm
        """
        analyzer = TerrainAnalyzer()
        steep_slope = TerrainProduct(
            product_id="SLOPE-20DEG",
            product_type="slope_map",
            data=np.full(self._SHAPE, 20.0, dtype=np.float32),
            extent=_EXTENT,
            metadata=_meta(),
        )
        hazard = analyzer.compute_hazard_map(steep_slope, self._zero_roughness_product())

        assert float(hazard.data.mean()) == pytest.approx(0.625, abs=1e-4)
        assert float(hazard.data.mean()) > 0.5


# ---------------------------------------------------------------------------
# CandidateScorer tests
# ---------------------------------------------------------------------------


class TestCandidateScorer:
    def test_scorer_returns_ranked_candidate(self) -> None:
        """A single HC-passed candidate produces exactly one RankedCandidate."""
        scorer = _scorer()
        result = scorer.rank([_candidate()], {})

        assert len(result) == 1
        assert isinstance(result[0], RankedCandidate)

    def test_scorer_score_in_range(self) -> None:
        """Every component score and total_score must lie in [0.0, 1.0]."""
        scorer = _scorer()
        ranked = scorer.rank([_candidate()], {})[0]

        for attr in (
            "science_score",
            "energy_score",
            "thermal_score",
            "communication_score",
            "risk_score",
            "total_score",
        ):
            val = getattr(ranked, attr)
            assert 0.0 <= val <= 1.0, f"{attr} = {val} is outside [0, 1]"

    def test_scorer_higher_sun_better_energy_score(self) -> None:
        """Higher average illumination_fraction must yield a higher energy_score.

        score_energy returns avg_illumination directly when illumination data
        is present (scorer.py §score_energy); 0.80 > 0.10, so HIGH > LOW.
        """
        scorer = _scorer()
        cand_lo = _candidate("LOW")
        cand_hi = _candidate("HIGH")

        timestamps = [_utc_dt(), _utc_dt()]

        env_lo = EnvironmentalDataProduct(
            illumination=IlluminationTimeSeries(
                pixel_lat=-85.0,
                pixel_lon=1.0,
                timestamps=timestamps,
                illumination_fraction=[0.10, 0.10],
                is_historical=True,
                metadata=_meta(),
            )
        )
        env_hi = EnvironmentalDataProduct(
            illumination=IlluminationTimeSeries(
                pixel_lat=-85.0,
                pixel_lon=1.0,
                timestamps=timestamps,
                illumination_fraction=[0.80, 0.80],
                is_historical=True,
                metadata=_meta(),
            )
        )

        ranked_lo = scorer.rank([cand_lo], {"LOW": env_lo})[0]
        ranked_hi = scorer.rank([cand_hi], {"HIGH": env_hi})[0]

        assert ranked_hi.energy_score > ranked_lo.energy_score

    def test_scorer_uncertainty_propagation_empty_env(self) -> None:
        """With no environmental data the scorer falls back to high-uncertainty
        defaults for every component → propagated score_uncertainty must be > 0.
        """
        scorer = _scorer()
        ranked = scorer.rank([_candidate()], {})[0]

        assert ranked.score_uncertainty > 0.0
