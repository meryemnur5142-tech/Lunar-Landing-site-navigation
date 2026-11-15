"""
Tests for POST /efficiency/sensitivity endpoint.

Covers:
  1. 200 with no overrides — behaves like a baseline run
  2. 200 with solar_elevation_deg override — delta_vs_baseline is populated
  3. 404 for an unknown candidate_id
  4. Override values actually change efficiency (at least one window differs)
"""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    from apps.ground_control.api.main import app
    client = TestClient(app)
    _API_AVAILABLE = True
except RuntimeError:
    _API_AVAILABLE = False
    client = None  # type: ignore

pytestmark = pytest.mark.skipif(
    not _API_AVAILABLE,
    reason="httpx2 not installed — run: pip install httpx2",
)

_KNOWN_ID = "SP-006"
_UNKNOWN_ID = "SP-999"
_URL = "/efficiency/sensitivity"


# ---------------------------------------------------------------------------
# 1. No overrides — should return 200 and all delta_vs_baseline values = 0.0
# ---------------------------------------------------------------------------

class TestSensitivityNoOverrides:
    def test_returns_200(self):
        r = client.post(_URL, json={"candidate_id": _KNOWN_ID})
        assert r.status_code == 200

    def test_response_shape(self):
        body = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        assert body["candidate_id"] == _KNOWN_ID
        assert body["crater_name"] == "Malapert A"
        assert len(body["windows"]) == 4
        assert "recommended_window_id" in body
        assert "factor_weights" in body
        assert "delta_vs_baseline" in body

    def test_factor_weights_correct(self):
        body = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        fw = body["factor_weights"]
        assert fw["terrain"] == pytest.approx(0.35)
        assert fw["science"] == pytest.approx(0.25)
        assert fw["window"] == pytest.approx(0.40)

    def test_no_overrides_zero_deltas(self):
        """Without overrides the result equals baseline, so all deltas must be 0."""
        body = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        for delta in body["delta_vs_baseline"].values():
            assert delta == pytest.approx(0.0), (
                f"Expected 0.0 delta without overrides, got {delta}"
            )

    def test_recommended_window_is_one_of_windows(self):
        body = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        window_ids = {w["window_id"] for w in body["windows"]}
        assert body["recommended_window_id"] in window_ids


# ---------------------------------------------------------------------------
# 2. solar_elevation_deg override — delta_vs_baseline should be populated
# ---------------------------------------------------------------------------

class TestSensitivitySolarOverride:
    _PAYLOAD = {
        "candidate_id": _KNOWN_ID,
        "overrides": {"solar_elevation_deg": 5.0},
    }

    def test_returns_200(self):
        r = client.post(_URL, json=self._PAYLOAD)
        assert r.status_code == 200

    def test_delta_vs_baseline_populated(self):
        """When solar_elevation_deg is overridden the deltas should be non-trivial."""
        body = client.post(_URL, json=self._PAYLOAD).json()
        assert len(body["delta_vs_baseline"]) == 4

    def test_delta_keys_match_window_ids(self):
        body = client.post(_URL, json=self._PAYLOAD).json()
        window_ids = {w["window_id"] for w in body["windows"]}
        assert set(body["delta_vs_baseline"].keys()) == window_ids

    def test_efficiency_changes_with_solar_override(self):
        """A higher solar elevation should change at least one window's efficiency."""
        baseline = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        overridden = client.post(_URL, json=self._PAYLOAD).json()

        baseline_eff = {w["window_id"]: w["efficiency_pct"] for w in baseline["windows"]}
        overridden_eff = {w["window_id"]: w["efficiency_pct"] for w in overridden["windows"]}

        changed = any(
            overridden_eff[wid] != baseline_eff[wid] for wid in baseline_eff
        )
        assert changed, "solar_elevation_deg override should change at least one window's efficiency"


# ---------------------------------------------------------------------------
# 3. 404 for unknown candidate_id
# ---------------------------------------------------------------------------

class TestSensitivity404:
    def test_unknown_candidate_returns_404(self):
        r = client.post(_URL, json={"candidate_id": _UNKNOWN_ID})
        assert r.status_code == 404

    def test_404_error_detail_mentions_candidate(self):
        body = client.post(_URL, json={"candidate_id": _UNKNOWN_ID}).json()
        assert _UNKNOWN_ID in body["detail"]


# ---------------------------------------------------------------------------
# 4. Override values actually change efficiency
# ---------------------------------------------------------------------------

class TestSensitivityChangesEfficiency:
    def test_terrain_override_changes_efficiency(self):
        """Changing max_slope_deg should produce different terrain score and efficiency."""
        baseline = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        # SP-006 has max_slope_deg=3.5; set to 11.0 — much steeper, efficiency drops
        overridden = client.post(
            _URL,
            json={"candidate_id": _KNOWN_ID, "overrides": {"max_slope_deg": 11.0}},
        ).json()

        baseline_effs = [w["efficiency_pct"] for w in baseline["windows"]]
        overridden_effs = [w["efficiency_pct"] for w in overridden["windows"]]
        assert baseline_effs != overridden_effs, (
            "max_slope_deg override should produce different efficiency values"
        )

    def test_delta_vs_baseline_matches_efficiency_difference(self):
        """delta_vs_baseline must equal override_eff - baseline_eff for each window."""
        baseline = client.post(_URL, json={"candidate_id": _KNOWN_ID}).json()
        overridden = client.post(
            _URL,
            json={
                "candidate_id": _KNOWN_ID,
                "overrides": {
                    "solar_elevation_deg": 5.0,
                    "max_slope_deg": 11.0,
                },
            },
        ).json()

        baseline_eff = {w["window_id"]: w["efficiency_pct"] for w in baseline["windows"]}
        for w in overridden["windows"]:
            expected_delta = round(w["efficiency_pct"] - baseline_eff[w["window_id"]], 2)
            actual_delta = overridden["delta_vs_baseline"][w["window_id"]]
            assert actual_delta == pytest.approx(expected_delta, abs=1e-6), (
                f"Window {w['window_id']}: expected delta {expected_delta}, got {actual_delta}"
            )

    def test_all_overrides_combined(self):
        """Full override payload with all fields returns a valid 200 response."""
        payload = {
            "candidate_id": "SP-002",
            "overrides": {
                "solar_elevation_deg": 5.0,
                "earth_elevation_deg": 15.0,
                "descent_angle_deg": 8.0,
                "delta_v_penalty_ms": 0.0,
                "max_slope_deg": 3.5,
                "psr_access_fraction": 0.18,
                "rock_abundance": 0.05,
            },
        }
        r = client.post(_URL, json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["candidate_id"] == "SP-002"
        assert len(body["windows"]) == 4
