"""Request / response schemas for the LUNA-AI Ground Control API."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


# ---------------------------------------------------------------------------
# Candidate input (POST /evaluate)
# ---------------------------------------------------------------------------

class CandidateInput(BaseModel):
    candidate_id: str
    crater_name: str
    center_lat: float = Field(..., ge=-90.0, le=90.0)
    center_lon: float = Field(..., ge=0.0, le=360.0)
    diameter_km: float = Field(..., gt=0.0)
    max_slope_deg: float = Field(..., ge=0.0)
    roughness_rms_m: float = Field(..., ge=0.0)
    rock_abundance: float = Field(..., ge=0.0, le=1.0)
    psr_access_fraction: float = Field(..., ge=0.0, le=1.0)


class ScoringWeightsInput(BaseModel):
    science: float = 0.35
    energy: float = 0.25
    thermal: float = 0.15
    communication: float = 0.10
    risk: float = 0.15


class EvaluateRequest(BaseModel):
    candidates: List[CandidateInput]
    weights: Optional[ScoringWeightsInput] = None


# ---------------------------------------------------------------------------
# Pipeline results (GET /candidates, POST /evaluate)
# ---------------------------------------------------------------------------

class RejectedCandidate(BaseModel):
    candidate_id: str
    reason: str


class RankedCandidateResponse(BaseModel):
    rank: int
    candidate_id: str
    crater_name: Optional[str]
    total_score: float
    score_uncertainty: float
    science_score: float
    energy_score: float
    thermal_score: float
    communication_score: float
    risk_score: float
    max_slope_deg: float
    roughness_rms_m: float
    psr_access_fraction: float
    rock_abundance: float


class EvaluateResponse(BaseModel):
    total_candidates: int
    passed_hc: int
    rejected_hc: int
    rejected: List[RejectedCandidate]
    ranked: List[RankedCandidateResponse]
    recommendation: Optional[str] = None  # top-ranked candidate_id


# ---------------------------------------------------------------------------
# Hard constraints list (GET /constraints)
# ---------------------------------------------------------------------------

class ConstraintResponse(BaseModel):
    constraint_id: str
    name: str
    description: str
    threshold: float
    unit: str
    operator: str


# ---------------------------------------------------------------------------
# Mission status (GET /mission/status)
# ---------------------------------------------------------------------------

class MissionStatusResponse(BaseModel):
    mission_id: str
    phase: str
    phase_description: str
    safety_state: str
    tbd_open_count: int
    note: str


# ---------------------------------------------------------------------------
# Audit history (GET /history, GET /history/{run_id})
# ---------------------------------------------------------------------------

class RunSummaryResponse(BaseModel):
    run_id: str
    timestamp: str
    mode: str
    recommendation: Optional[str]
    total_candidates: int
    passed_hc: int
    rejected_hc: int


class RankedEntryResponse(BaseModel):
    rank: int
    candidate_id: str
    total_score: float


class RunDetailResponse(BaseModel):
    run_id: str
    timestamp: str
    mode: str
    recommendation: Optional[str]
    total_candidates: int
    passed_hc: int
    rejected_hc: int
    crater_ids: List[str]
    weights: dict
    ranked: List[RankedEntryResponse]


# ---------------------------------------------------------------------------
# Comparison (POST /api/v1/compare)
# ---------------------------------------------------------------------------

class RankedScenarioItem(BaseModel):
    rank: int
    candidate_id: str
    crater_name: Optional[str]
    total_score: float


class ScenarioResult(BaseModel):
    label: str
    weights: ScoringWeightsInput
    ranked: List[RankedScenarioItem]


class RankChangeItem(BaseModel):
    candidate_id: str
    crater_name: str
    rank_a: int
    rank_b: int
    delta: int
    direction: str  # "up" | "down" | "same"


class CompareRequest(BaseModel):
    weights_a: ScoringWeightsInput = ScoringWeightsInput(
        science=0.50, energy=0.20, thermal=0.10, communication=0.10, risk=0.10
    )
    weights_b: ScoringWeightsInput = ScoringWeightsInput(
        science=0.20, energy=0.20, thermal=0.20, communication=0.10, risk=0.30
    )
    label_a: str = "Bilim Odakli"
    label_b: str = "Guvenlik Odakli"


class CompareResponse(BaseModel):
    scenario_a: ScenarioResult
    scenario_b: ScenarioResult
    rank_changes: List[RankChangeItem]
    top_pick_changed: bool
    top_pick_a: str
    top_pick_b: str

