"""
API route tests using FastAPI TestClient (no running server required).

Covers all 5 endpoints:
  GET  /health
  GET  /api/v1/candidates
  POST /api/v1/evaluate
  GET  /api/v1/constraints
  GET  /api/v1/mission/status

Requires: pip install httpx2
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


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_status_ok(self):
        body = client.get("/health").json()
        assert body["status"] == "ok"

    def test_version_present(self):
        body = client.get("/health").json()
        assert "version" in body


# ---------------------------------------------------------------------------
# GET /api/v1/candidates  (demo pipeline)
# ---------------------------------------------------------------------------

class TestCandidatesEndpoint:
    def test_returns_200(self):
        r = client.get("/api/v1/candidates")
        assert r.status_code == 200

    def test_total_is_five(self):
        body = client.get("/api/v1/candidates").json()
        assert body["total_candidates"] == 5

    def test_two_rejected(self):
        body = client.get("/api/v1/candidates").json()
        assert body["rejected_hc"] == 2

    def test_three_ranked(self):
        body = client.get("/api/v1/candidates").json()
        assert len(body["ranked"]) == 3

    def test_ranked_descending(self):
        body = client.get("/api/v1/candidates").json()
        scores = [r["total_score"] for r in body["ranked"]]
        assert scores == sorted(scores, reverse=True)

    def test_recommendation_is_top_ranked(self):
        body = client.get("/api/v1/candidates").json()
        assert body["recommendation"] == body["ranked"][0]["candidate_id"]

    def test_rejection_cites_hc_codes(self):
        body = client.get("/api/v1/candidates").json()
        reasons = " ".join(r["reason"] for r in body["rejected"])
        assert "HC-001" in reasons
        assert "HC-003" in reasons


# ---------------------------------------------------------------------------
# POST /api/v1/evaluate  (caller-supplied candidates)
# ---------------------------------------------------------------------------

_GOOD = {
    "candidate_id": "T-001",
    "crater_name": "TestCrater",
    "center_lat": -88.0,
    "center_lon": 0.0,
    "diameter_km": 20.0,
    "max_slope_deg": 8.0,
    "roughness_rms_m": 0.2,
    "rock_abundance": 0.10,
    "psr_access_fraction": 0.60,
}

_BAD_SLOPE = {**_GOOD, "candidate_id": "T-002", "max_slope_deg": 20.0}


class TestEvaluateEndpoint:
    def test_single_good_candidate_passes(self):
        r = client.post("/api/v1/evaluate", json={"candidates": [_GOOD]})
        assert r.status_code == 200
        body = r.json()
        assert body["passed_hc"] == 1
        assert body["rejected_hc"] == 0
        assert len(body["ranked"]) == 1

    def test_bad_slope_candidate_rejected(self):
        r = client.post("/api/v1/evaluate", json={"candidates": [_BAD_SLOPE]})
        assert r.status_code == 200
        body = r.json()
        assert body["passed_hc"] == 0
        assert body["rejected_hc"] == 1
        assert "HC-001" in body["rejected"][0]["reason"]

    def test_mixed_candidates(self):
        r = client.post("/api/v1/evaluate", json={"candidates": [_GOOD, _BAD_SLOPE]})
        body = r.json()
        assert body["passed_hc"] == 1
        assert body["rejected_hc"] == 1

    def test_empty_candidates_returns_422(self):
        r = client.post("/api/v1/evaluate", json={"candidates": []})
        assert r.status_code == 422

    def test_custom_weights_accepted(self):
        payload = {
            "candidates": [_GOOD],
            "weights": {
                "science": 0.50,
                "energy": 0.20,
                "thermal": 0.10,
                "communication": 0.10,
                "risk": 0.10,
            },
        }
        r = client.post("/api/v1/evaluate", json=payload)
        assert r.status_code == 200
        assert len(r.json()["ranked"]) == 1

    def test_scores_in_range(self):
        r = client.post("/api/v1/evaluate", json={"candidates": [_GOOD]})
        rc = r.json()["ranked"][0]
        for field in ("total_score", "science_score", "energy_score",
                      "thermal_score", "communication_score", "risk_score"):
            assert 0.0 <= rc[field] <= 1.0, f"{field} out of range"


# ---------------------------------------------------------------------------
# GET /api/v1/constraints
# ---------------------------------------------------------------------------

class TestConstraintsEndpoint:
    def test_returns_200(self):
        assert client.get("/api/v1/constraints").status_code == 200

    def test_at_least_three_constraints(self):
        body = client.get("/api/v1/constraints").json()
        assert len(body) >= 3

    def test_constraint_has_required_fields(self):
        body = client.get("/api/v1/constraints").json()
        for c in body:
            assert "constraint_id" in c
            assert "name" in c
            assert "threshold" in c

    def test_hc001_present(self):
        ids = [c["constraint_id"] for c in client.get("/api/v1/constraints").json()]
        assert "HC-001" in ids


# ---------------------------------------------------------------------------
# GET /api/v1/mission/status
# ---------------------------------------------------------------------------

class TestMissionStatusEndpoint:
    def test_returns_200(self):
        assert client.get("/api/v1/mission/status").status_code == 200

    def test_has_phase_and_safety_state(self):
        body = client.get("/api/v1/mission/status").json()
        assert "phase" in body
        assert "safety_state" in body

    def test_tbd_count_positive(self):
        body = client.get("/api/v1/mission/status").json()
        assert body["tbd_open_count"] > 0
