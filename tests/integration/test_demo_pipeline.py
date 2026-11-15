"""
End-to-end pipeline validation using estimated south-pole candidate data.

These tests verify that the HC filter + scorer stack produces physically
reasonable results for representative lunar south-pole landing sites.
They do NOT require real orbital data products.

Expected outcomes (from published orbital surveys):
  SP-003 (Nobile)         — rejected: rock_abundance > HC-003 limit
  SP-005 (Unnamed Ridge)  — rejected: max_slope_deg > HC-001 limit
  SP-001 (Shackleton)     — ranked last among survivors: highest thermal risk
                             (PSR 82% -> long dark exposure)
  SP-006 (Malapert A)     — ranked first on default weights: best terrain +
                             lowest thermal risk (PSR only 18%)
"""

from __future__ import annotations

import pytest

from luna_ai.pipeline import run_pipeline
from luna_ai.sample_data import CANDIDATES


@pytest.fixture(scope="module")
def result():
    return run_pipeline(CANDIDATES)


class TestHardConstraintFilter:
    def test_two_candidates_rejected(self, result):
        assert result.rejected_hc == 2

    def test_five_candidates_pass(self, result):
        # SP-001,002,004,006,007 pass; SP-003 and SP-005 fail
        assert result.passed_hc == 5

    def test_nobile_rejected_rock_abundance(self, result):
        rejected_ids = {cid for cid, _ in result.rejection_summary}
        assert "SP-003" in rejected_ids

    def test_unnamed_ridge_rejected_slope(self, result):
        rejected_ids = {cid for cid, _ in result.rejection_summary}
        assert "SP-005" in rejected_ids

    def test_rejection_reasons_cite_hc_codes(self, result):
        reasons = {cid: reason for cid, reason in result.rejection_summary}
        assert "HC-003" in reasons["SP-003"]
        assert "HC-001" in reasons["SP-005"]


class TestScoringAndRanking:
    def test_five_ranked_candidates(self, result):
        # All five HC-passing candidates are scored and ranked
        assert len(result.ranked) == 5

    def test_all_scores_in_range(self, result):
        for rc in result.ranked:
            assert 0.0 <= rc.total_score <= 1.0
            assert 0.0 <= rc.score_uncertainty <= 1.0
            assert 0.0 <= rc.science_score <= 1.0
            assert 0.0 <= rc.risk_score <= 1.0

    def test_ranked_descending(self, result):
        scores = [rc.total_score for rc in result.ranked]
        assert scores == sorted(scores, reverse=True)

    def test_malapert_ranked_first(self, result):
        # Malapert A (SP-006): flattest slope (3.5 deg), lowest rock abundance (5%),
        # best risk score, highest thermal score (PSR only 18% -> minimal dark exposure)
        # -> wins on default weights (science=0.35, energy=0.25, thermal=0.15, risk=0.15)
        assert result.ranked[0].candidate.candidate_id == "SP-006"

    def test_shackleton_ranked_last_among_survivors(self, result):
        # Shackleton (SP-001): highest PSR access (82%) -> highest thermal risk
        # -> lowest thermal score -> comes last despite top science value
        assert result.ranked[-1].candidate.candidate_id == "SP-001"

    def test_higher_psr_gets_lower_thermal_score(self, result):
        # Thermal score = 1 - psr_access_fraction (proxy until thermal model available)
        # Shackleton PSR=82% should have lower thermal score than Haworth PSR=55%
        ranked_map = {rc.candidate.candidate_id: rc for rc in result.ranked}
        assert ranked_map["SP-001"].thermal_score < ranked_map["SP-002"].thermal_score

    def test_flatter_site_gets_better_risk_score(self, result):
        ranked_map = {rc.candidate.candidate_id: rc for rc in result.ranked}
        # Haworth (7.3 deg) vs Shackleton (12.5 deg)
        assert ranked_map["SP-002"].risk_score > ranked_map["SP-001"].risk_score
