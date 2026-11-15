"""SQLite-backed audit store for LUNA-AI pipeline evaluation runs.

Thread-safe: each method opens and closes its own connection so this is safe
under multi-threaded FastAPI / uvicorn workers.  No external dependencies —
stdlib sqlite3 only.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB path — created at import-time resolution; actual dir is created lazily.
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
# Repo root is three levels up: data-platform/persistence/audit_store.py
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_DEFAULT_DB_PATH = os.path.join(_REPO_ROOT, "data", "luna_ai_history.db")

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id              TEXT PRIMARY KEY,
    timestamp           TEXT NOT NULL,
    mode                TEXT NOT NULL,
    crater_ids          TEXT NOT NULL,
    weights             TEXT NOT NULL,
    total_candidates    INTEGER NOT NULL,
    passed_hc           INTEGER NOT NULL,
    rejected_hc         INTEGER NOT NULL,
    ranked              TEXT NOT NULL,
    recommendation      TEXT
);
"""


class SQLiteAuditStore:
    """Persist and query pipeline evaluation runs in a local SQLite database.

    Parameters
    ----------
    db_path:
        Absolute path to the SQLite file.  The containing directory is created
        at first write if it does not already exist.
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a new connection and ensure the schema exists."""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_run(self, result: Any, mode: str, weights_dict: dict) -> str:
        """Persist a PipelineResult and return a fresh run_id (uuid4 string).

        Parameters
        ----------
        result:
            A ``luna_ai.pipeline.PipelineResult`` instance.
        mode:
            ``"demo"`` for the built-in sample pipeline, ``"user"`` for
            caller-supplied candidates.
        weights_dict:
            Scoring weights as a plain dict
            ``{"science": float, "energy": float, ...}``.

        Returns
        -------
        str
            The newly created run_id.
        """
        run_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()

        # Build serialisable ranked list
        ranked_list = []
        for i, rc in enumerate(result.ranked, start=1):
            ranked_list.append(
                {
                    "rank": i,
                    "candidate_id": rc.candidate.candidate_id,
                    "total_score": round(rc.total_score, 6),
                }
            )

        crater_ids = [rc.candidate.candidate_id for rc in result.ranked]
        # Also add rejected candidate ids so we have the full picture
        for cid, _ in result.rejection_summary:
            if cid not in crater_ids:
                crater_ids.append(cid)

        recommendation = result.ranked[0].candidate.candidate_id if result.ranked else None

        row = (
            run_id,
            ts,
            mode,
            json.dumps(crater_ids),
            json.dumps(weights_dict),
            result.total_candidates,
            result.passed_hc,
            result.rejected_hc,
            json.dumps(ranked_list),
            recommendation,
        )

        sql = """
        INSERT INTO evaluation_runs
            (run_id, timestamp, mode, crater_ids, weights,
             total_candidates, passed_hc, rejected_hc, ranked, recommendation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn = self._connect()
        try:
            conn.execute(sql, row)
            conn.commit()
        finally:
            conn.close()

        return run_id

    def get_run(self, run_id: str) -> dict | None:
        """Return one run as a dict, or ``None`` if not found."""
        sql = "SELECT * FROM evaluation_runs WHERE run_id = ?"
        conn = self._connect()
        try:
            cur = conn.execute(sql, (run_id,))
            row = cur.fetchone()
        finally:
            conn.close()

        if row is None:
            return None
        return _row_to_dict(row)

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Return the most recent runs, newest first.

        Parameters
        ----------
        limit:
            Maximum number of rows to return.
        offset:
            Number of rows to skip (for pagination).
        """
        sql = (
            "SELECT * FROM evaluation_runs "
            "ORDER BY timestamp DESC "
            "LIMIT ? OFFSET ?"
        )
        conn = self._connect()
        try:
            cur = conn.execute(sql, (limit, offset))
            rows = cur.fetchall()
        finally:
            conn.close()

        return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    # Deserialise JSON columns
    for col in ("crater_ids", "weights", "ranked"):
        if d.get(col):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
