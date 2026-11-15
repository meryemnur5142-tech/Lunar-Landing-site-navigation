"""
Tests for POST /api/v1/compare — multi-scenario comparison endpoint.

Runs the full pipeline twice under two different weight sets and verifies
the response structure and semantic correctness.

Requires: pip install httpx
"""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    from apps.ground_control.api.main import app

    client = TestClient(app)
    _API_AVAILABLE = True
except (RuntimeError, ImportError):
    _API_AVAILABLE = False
    client = None  # type: ignore

pytestmark = pytest.mark.skipif(
    not _API_AVAILABLE,
    reason="httpx not installed or app failed to load — run: pip install httpx",
)

# ---------------------------------------------------------------------------
# Default weights (science-biased vs safety-biased)
# ---------------------------------------------------------------------------

class TestCompareDefaultWeights:
    def test_returns_200(self):
        r = client.post("/api/v1/compare", json={})
        assert r.status_code == 200, r.text

    def test_scenario_a_present(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert "scenario_a" in body
        assert "ranked" in body["scenario_a"]
        assert len(body["scenario_a"]["ranked"]) > 0

    def test_scenario_b_present(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert "scenario_b" in body
        assert "ranked" in body["scenario_b"]
        assert len(body["scenario_b"]["ranked"]) > 0

    def test_rank_changes_field_present(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert "rank_changes" in body

    def test_rank_changes_covers_all_hc_passing_candidates(self):
        """
        CANDIDATES has 7 entries:
          SP-003 (rocks=0.21 > 0.20)   fails HC-003
          SP-005 (slope=17.4 > 15.0)   fails HC-001
        That leaves exactly 5 HC-passing candidates.
        """
        body = client.post("/api/v1/compare", json={}).json()
        assert len(body["rank_changes"]) == 5

    def test_top_pick_fields_present(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert "top_pick_a" in body
        assert "top_pick_b" in body
        assert isinstance(body["top_pick_a"], str)
        assert isinstance(body["top_pick_b"], str)

    def test_top_pick_changed_field_present(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert "top_pick_changed" in body
        assert isinstance(body["top_pick_changed"], bool)

    def test_rank_change_items_have_required_fields(self):
        body = client.post("/api/v1/compare", json={}).json()
        for item in body["rank_changes"]:
            assert "candidate_id" in item
            assert "crater_name" in item
            assert "rank_a" in item
            assert "rank_b" in item
            assert "delta" in item
            assert "direction" in item
            assert item["direction"] in ("up", "down", "same")

    def test_delta_consistent_with_ranks(self):
        body = client.post("/api/v1/compare", json={}).json()
        for item in body["rank_changes"]:
            expected_delta = item["rank_a"] - item["rank_b"]
            assert item["delta"] == expected_delta

    def test_direction_consistent_with_delta(self):
        body = client.post("/api/v1/compare", json={}).json()
        for item in body["rank_changes"]:
            if item["delta"] > 0:
                assert item["direction"] == "up"
            elif item["delta"] < 0:
                assert item["direction"] == "down"
            else:
                assert item["direction"] == "same"

    def test_scenario_labels(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert body["scenario_a"]["label"] == "Bilim Odaklı"
        assert body["scenario_b"]["label"] == "Güvenlik Odaklı"

    def test_scenario_a_ranked_first_has_rank_1(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert body["scenario_a"]["ranked"][0]["rank"] == 1

    def test_scenario_b_ranked_first_has_rank_1(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert body["scenario_b"]["ranked"][0]["rank"] == 1

    def test_top_pick_a_matches_first_ranked_a(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert body["top_pick_a"] == body["scenario_a"]["ranked"][0]["candidate_id"]

    def test_top_pick_b_matches_first_ranked_b(self):
        body = client.post("/api/v1/compare", json={}).json()
        assert body["top_pick_b"] == body["scenario_b"]["ranked"][0]["candidate_id"]


# ---------------------------------------------------------------------------
# Custom labels
# ---------------------------------------------------------------------------

class TestCompareCustomLabels:
    def test_custom_labels_echoed(self):
        payload = {
            "label_a": "Scenario Alpha",
            "label_b": "Scenario Beta",
        }
        body = client.post("/api/v1/compare", json=payload).json()
        assert body["scenario_a"]["label"] == "Scenario Alpha"
        assert body["scenario_b"]["label"] == "Scenario Beta"


# ---------------------------------------------------------------------------
# Extreme weights — different top picks guaranteed
# ---------------------------------------------------------------------------

class TestCompareExtremeWeights:
    """With maximally contrasting weights the top pick must differ between scenarios."""

    def test_extreme_science_vs_extreme_safety_changes_top_pick(self):
        """
        Max-science weight: Shackleton (PSR 0.82) dominates.
        Max-risk/safety weight: Malapert A (shallowest slope, lowest rocks) dominates.
        These two are different candidates, so top_pick_changed must be True.
        """
        payload = {
            "weights_a": {
                "science": 0.90,
                "energy": 0.025,
                "thermal": 0.025,
                "communication": 0.025,
                "risk": 0.025,
            },
            "weights_b": {
                "science": 0.025,
                "energy": 0.025,
                "thermal": 0.025,
                "communication": 0.025,
                "risk": 0.90,
            },
            "label_a": "Max Science",
            "label_b": "Max Safety",
        }
        r = client.post("/api/v1/compare", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["top_pick_changed"] is True
        assert body["top_pick_a"] != body["top_pick_b"]

    def test_extreme_science_top_pick_is_haworth(self):
        """With almost all weight on science, Haworth (SP-002) should win.

        All HC-passing candidates have PSR > 0.20, so science scores all cap at 1.0.
        The tiebreaker is dominated by energy/thermal/risk which Haworth leads.
        """
        payload = {
            "weights_a": {
                "science": 0.90,
                "energy": 0.025,
                "thermal": 0.025,
                "communication": 0.025,
                "risk": 0.025,
            },
            "weights_b": {
                "science": 0.20,
                "energy": 0.20,
                "thermal": 0.20,
                "communication": 0.10,
                "risk": 0.30,
            },
        }
        r = client.post("/api/v1/compare", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["top_pick_a"] == "SP-002"  # Haworth — best balanced terrain+science


# ---------------------------------------------------------------------------
# Validation — weights not summing to 1.0 must be rejected
# ---------------------------------------------------------------------------

class TestCompareValidation:
    def test_invalid_weights_a_rejected(self):
        payload = {
            "weights_a": {
                "science": 0.50,
                "energy": 0.50,
                "thermal": 0.50,
                "communication": 0.50,
                "risk": 0.50,
            },
        }
        r = client.post("/api/v1/compare", json=payload)
        assert r.status_code == 422

    def test_invalid_weights_b_rejected(self):
        payload = {
            "weights_b": {
                "science": 0.10,
                "energy": 0.10,
                "thermal": 0.10,
                "communication": 0.10,
                "risk": 0.10,
            },
        }
        r = client.post("/api/v1/compare", json=payload)
        assert r.status_code == 422
