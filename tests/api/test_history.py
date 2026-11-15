"""
Tests for the evaluation history / audit log endpoints.

Covers:
  GET  /history              — returns 200 and a list
  GET  /history/{nonexistent} — returns 404
  POST /api/v1/evaluate → GET /history — at least one entry appears
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
    reason="httpx not installed — run: pip install httpx",
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_GOOD_CANDIDATE = {
    "candidate_id": "HIST-001",
    "crater_name": "HistoryCrater",
    "center_lat": -88.5,
    "center_lon": 10.0,
    "diameter_km": 15.0,
    "max_slope_deg": 7.0,
    "roughness_rms_m": 0.18,
    "rock_abundance": 0.08,
    "psr_access_fraction": 0.65,
}


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------

class TestHistoryList:
    def test_returns_200(self):
        r = client.get("/history")
        assert r.status_code == 200

    def test_returns_list(self):
        body = client.get("/history").json()
        assert isinstance(body, list)

    def test_limit_param_accepted(self):
        r = client.get("/history?limit=5&offset=0")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) <= 5

    def test_summary_fields_present(self):
        """Each entry in the list must have the RunSummaryResponse fields."""
        # Ensure at least one run exists first
        client.get("/api/v1/candidates")
        body = client.get("/history").json()
        if body:
            entry = body[0]
            for field in (
                "run_id", "timestamp", "mode",
                "total_candidates", "passed_hc", "rejected_hc",
            ):
                assert field in entry, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# GET /history/{run_id} — 404 path
# ---------------------------------------------------------------------------

class TestHistoryDetail404:
    def test_nonexistent_run_returns_404(self):
        r = client.get("/history/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404

    def test_404_body_has_detail(self):
        r = client.get("/history/no-such-run")
        assert r.status_code == 404
        assert "detail" in r.json()


# ---------------------------------------------------------------------------
# POST /api/v1/evaluate → GET /history  (integration)
# ---------------------------------------------------------------------------

class TestHistoryAfterEvaluate:
    def test_evaluate_then_history_has_entry(self):
        # Trigger a user-mode evaluation run
        resp = client.post("/api/v1/evaluate", json={"candidates": [_GOOD_CANDIDATE]})
        assert resp.status_code == 200

        # The audit log should now contain at least one entry
        history = client.get("/history").json()
        assert len(history) >= 1

    def test_evaluate_run_appears_as_user_mode(self):
        client.post("/api/v1/evaluate", json={"candidates": [_GOOD_CANDIDATE]})
        history = client.get("/history").json()
        # The most recent entry should be a user-mode run
        user_runs = [h for h in history if h["mode"] == "user"]
        assert len(user_runs) >= 1

    def test_detail_endpoint_returns_run(self):
        """After an evaluate call, the returned run_id resolves via GET /history/{id}."""
        # Kick off a run so there is at least one entry
        client.post("/api/v1/evaluate", json={"candidates": [_GOOD_CANDIDATE]})
        history = client.get("/history").json()
        assert history, "No history entries found after evaluate call"

        run_id = history[0]["run_id"]
        detail_resp = client.get(f"/history/{run_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["run_id"] == run_id
        assert "ranked" in detail
        assert "weights" in detail
        assert "crater_ids" in detail

    def test_demo_pipeline_also_logged(self):
        """GET /api/v1/candidates (demo mode) should also persist a run."""
        client.get("/api/v1/candidates")
        history = client.get("/history").json()
        demo_runs = [h for h in history if h["mode"] == "demo"]
        assert len(demo_runs) >= 1
