"""POST /api/v1/compare — run pipeline twice with different scoring weight sets."""

from __future__ import annotations

import copy

from fastapi import APIRouter, HTTPException

from domain.mission.models import ScoringWeights
from luna_ai.pipeline import run_pipeline
from luna_ai.sample_data import CANDIDATES

from ..schemas import (
    CompareRequest,
    CompareResponse,
    RankChangeItem,
    RankedScenarioItem,
    ScenarioResult,
    ScoringWeightsInput,
)

router = APIRouter(prefix="/api/v1", tags=["Compare"])


def _build_weights(w: ScoringWeightsInput, label: str) -> ScoringWeights:
    """Convert API schema weights to domain ScoringWeights, raising HTTP 422 on error."""
    try:
        return ScoringWeights(
            science=w.science,
            energy=w.energy,
            thermal=w.thermal,
            communication=w.communication,
            risk=w.risk,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{label} weights invalid: {exc}") from exc


def _run_scenario(weights: ScoringWeights) -> dict[str, dict]:
    """Run the full pipeline on a fresh copy of CANDIDATES and return a lookup map.

    Returns a dict keyed by candidate_id:
        { candidate_id: {rank, candidate_id, crater_name, total_score} }

    Only HC-passing candidates appear in the returned map.
    """
    # Deep-copy so repeated calls don't interfere with each other
    result = run_pipeline(copy.deepcopy(CANDIDATES), weights=weights)
    ranked_map: dict[str, dict] = {}
    for i, rc in enumerate(result.ranked, start=1):
        c = rc.candidate
        ranked_map[c.candidate_id] = {
            "rank": i,
            "candidate_id": c.candidate_id,
            "crater_name": c.crater.name,
            "total_score": round(rc.total_score, 4),
        }
    return ranked_map


@router.post("/compare", response_model=CompareResponse)
def compare_scenarios(body: CompareRequest) -> CompareResponse:
    """Run the evaluation pipeline twice — once per weight set — and return a delta report.

    Both runs use the same built-in CANDIDATES from ``luna_ai.sample_data``.
    Only candidates that passed hard constraints in **both** runs appear in the
    ``rank_changes`` list and the per-scenario ``ranked`` arrays.

    The ``rank_changes`` list covers every common HC-passing candidate and shows
    how its rank shifted between Scenario A and Scenario B.  ``direction`` is
    ``"up"`` when the rank improved in B (lower rank number), ``"down"`` when it
    worsened, and ``"same"`` when it did not change.
    """
    w_a = _build_weights(body.weights_a, "weights_a")
    w_b = _build_weights(body.weights_b, "weights_b")

    ranked_a = _run_scenario(w_a)
    ranked_b = _run_scenario(w_b)

    # Intersection: candidates that passed HC in both runs
    common_ids = set(ranked_a.keys()) & set(ranked_b.keys())

    # Build per-scenario ranked lists (only common candidates, in rank order)
    scenario_a_ranked = sorted(
        [v for cid, v in ranked_a.items() if cid in common_ids],
        key=lambda x: x["rank"],
    )
    scenario_b_ranked = sorted(
        [v for cid, v in ranked_b.items() if cid in common_ids],
        key=lambda x: x["rank"],
    )

    # Re-rank within the common set so positions are contiguous
    for new_rank, item in enumerate(scenario_a_ranked, start=1):
        item["rank"] = new_rank
    for new_rank, item in enumerate(scenario_b_ranked, start=1):
        item["rank"] = new_rank

    # Rebuild lookup after re-ranking
    a_by_id = {item["candidate_id"]: item for item in scenario_a_ranked}
    b_by_id = {item["candidate_id"]: item for item in scenario_b_ranked}

    # Build rank_changes list sorted by Scenario A rank
    rank_changes: list[RankChangeItem] = []
    for cid in sorted(common_ids, key=lambda cid: a_by_id[cid]["rank"]):
        a = a_by_id[cid]
        b = b_by_id[cid]
        # delta > 0 means rank improved (lower number) in B → "up"
        delta = a["rank"] - b["rank"]
        direction = "up" if delta > 0 else ("down" if delta < 0 else "same")
        rank_changes.append(
            RankChangeItem(
                candidate_id=cid,
                crater_name=a["crater_name"] or "",
                rank_a=a["rank"],
                rank_b=b["rank"],
                delta=delta,
                direction=direction,
            )
        )

    top_pick_a = scenario_a_ranked[0]["candidate_id"] if scenario_a_ranked else ""
    top_pick_b = scenario_b_ranked[0]["candidate_id"] if scenario_b_ranked else ""

    return CompareResponse(
        scenario_a=ScenarioResult(
            label=body.label_a,
            weights=body.weights_a,
            ranked=[RankedScenarioItem(**item) for item in scenario_a_ranked],
        ),
        scenario_b=ScenarioResult(
            label=body.label_b,
            weights=body.weights_b,
            ranked=[RankedScenarioItem(**item) for item in scenario_b_ranked],
        ),
        rank_changes=rank_changes,
        top_pick_changed=top_pick_a != top_pick_b,
        top_pick_a=top_pick_a,
        top_pick_b=top_pick_b,
    )
