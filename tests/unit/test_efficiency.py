"""Unit tests for the landing efficiency calculator."""

from __future__ import annotations

import pytest

from luna_ai.sample_data import CANDIDATES
from mission_intelligence.efficiency.landing_efficiency import EfficiencyCalculator
from mission_intelligence.efficiency.spice_windows import SpiceWindowCalculator


@pytest.fixture
def calc():
    return EfficiencyCalculator()


@pytest.fixture
def haworth():
    return next(c for c in CANDIDATES if c.candidate_id == "SP-002")


@pytest.fixture
def malapert():
    return next(c for c in CANDIDATES if c.candidate_id == "SP-006")


class TestEfficiencyCalculator:
    def test_returns_four_windows(self, calc, haworth):
        windows = calc.compute_windows(haworth)
        assert len(windows) == 4

    def test_window_ids_are_unique(self, calc, haworth):
        windows = calc.compute_windows(haworth)
        ids = [w.window_id for w in windows]
        assert len(set(ids)) == 4

    def test_efficiency_in_range(self, calc, haworth):
        for w in calc.compute_windows(haworth):
            assert 85.0 <= w.efficiency_pct <= 99.0, (
                f"{w.label}: efficiency {w.efficiency_pct} out of [85, 99]"
            )

    def test_w1_best_efficiency(self, calc, haworth):
        windows = calc.compute_windows(haworth)
        effs = [w.efficiency_pct for w in windows]
        assert effs[0] == max(effs), "W-1 (best solar/comm) should have highest efficiency"

    def test_efficiency_decreases_with_window_index(self, calc, haworth):
        effs = [w.efficiency_pct for w in calc.compute_windows(haworth)]
        assert effs[0] >= effs[1] >= effs[2] >= effs[3]

    def test_flat_terrain_scores_higher_than_steep(self, calc, malapert):
        steep = next(c for c in CANDIDATES if c.candidate_id == "SP-001")  # Shackleton 12.5°
        flat_effs  = [w.efficiency_pct for w in calc.compute_windows(malapert)]
        steep_effs = [w.efficiency_pct for w in calc.compute_windows(steep)]
        assert flat_effs[0] > steep_effs[0], (
            "Malapert A (3.5° slope) W-1 should beat Shackleton (12.5°) W-1"
        )

    def test_conditions_dict_populated(self, calc, haworth):
        for w in calc.compute_windows(haworth):
            assert w.conditions, f"{w.label} has empty conditions dict"
            assert "solar" in w.conditions
            assert "earth" in w.conditions

    def test_dominant_factor_is_valid(self, calc, haworth):
        valid = {"solar", "communication", "terrain", "propellant"}
        for w in calc.compute_windows(haworth):
            assert w.dominant_factor in valid, (
                f"{w.label} dominant_factor '{w.dominant_factor}' not in {valid}"
            )

    def test_solar_flux_positive(self, calc, haworth):
        for w in calc.compute_windows(haworth):
            assert w.solar_flux_wm2 > 0

    def test_all_candidates_produce_windows(self, calc):
        for c in CANDIDATES:
            windows = calc.compute_windows(c)
            assert len(windows) == 4, f"{c.candidate_id} did not return 4 windows"


class TestSpiceWindowCalculatorFallback:
    def test_returns_fallback_without_kernels(self):
        calc = SpiceWindowCalculator()
        assert not calc.ready

    def test_fallback_emits_warning(self):
        calc = SpiceWindowCalculator()
        with pytest.warns(UserWarning, match="SPICE kernels not loaded"):
            windows = calc.compute_windows(lat=-89.9, lon=0.0)
        assert len(windows) == 4

    def test_fallback_windows_have_valid_solar(self):
        calc = SpiceWindowCalculator()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            windows = calc.compute_windows(lat=-89.9, lon=0.0)
        for w in windows:
            assert w.solar_elevation_deg > 0
