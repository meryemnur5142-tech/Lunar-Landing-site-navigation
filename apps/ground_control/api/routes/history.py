"""
GET /history       — list recent evaluation runs (paginated)
GET /history/{id}  — get one run detail
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas import RunSummaryResponse, RunDetailResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["History"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_audit_store():
    """FastAPI dependency that returns a shared SQLiteAuditStore instance.

    Import is deferred so a missing data directory at startup does not crash
    the whole app — the store creates the directory on first write.
    """
    from data_platform.persistence.audit_store import SQLiteAuditStore  # noqa: PLC0415
    return SQLiteAuditStore()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/history", response_model=list[RunSummaryResponse])
def list_history(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    store=Depends(get_audit_store),
):
    """Return a paginated list of evaluation run summaries, newest first."""
    rows = store.list_runs(limit=limit, offset=offset)
    return [
        RunSummaryResponse(
            run_id=r["run_id"],
            timestamp=r["timestamp"],
            mode=r["mode"],
            recommendation=r.get("recommendation"),
            total_candidates=r["total_candidates"],
            passed_hc=r["passed_hc"],
            rejected_hc=r["rejected_hc"],
        )
        for r in rows
    ]


@router.get("/history/{run_id}", response_model=RunDetailResponse)
def get_history_run(run_id: str, store=Depends(get_audit_store)):
    """Return the full detail for a single evaluation run."""
    row = store.get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    return RunDetailResponse(
        run_id=row["run_id"],
        timestamp=row["timestamp"],
        mode=row["mode"],
        recommendation=row.get("recommendation"),
        total_candidates=row["total_candidates"],
        passed_hc=row["passed_hc"],
        rejected_hc=row["rejected_hc"],
        crater_ids=row.get("crater_ids", []),
        weights=row.get("weights", {}),
        ranked=row.get("ranked", []),
    )
