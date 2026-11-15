"""Importable shim for SQLiteAuditStore.

The canonical implementation lives in ``data-platform/persistence/audit_store.py``.
This module loads it via importlib so the hyphenated directory name does not
prevent normal ``from data_platform.persistence.audit_store import ...`` imports.

If the canonical file cannot be found (e.g. in a stripped install), the full
implementation is reproduced inline below so this package is always self-contained.
"""

from __future__ import annotations

import importlib.util
import os as _os

_CANONICAL = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "data-platform", "persistence", "audit_store.py",
)

if _os.path.exists(_CANONICAL):
    _spec = importlib.util.spec_from_file_location(
        "data_platform.persistence.audit_store_impl", _CANONICAL
    )
    _mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    SQLiteAuditStore = _mod.SQLiteAuditStore
    _row_to_dict = _mod._row_to_dict
else:
    # ---------------------------------------------------------------------------
    # Inline fallback — identical to data-platform/persistence/audit_store.py
    # ---------------------------------------------------------------------------
    import json as _json
    import logging as _logging
    import sqlite3 as _sqlite3
    import uuid as _uuid
    from datetime import datetime as _datetime, timezone as _timezone
    from typing import Any as _Any

    _logger = _logging.getLogger(__name__)

    _HERE2 = _os.path.dirname(_os.path.abspath(__file__))
    _REPO_ROOT2 = _os.path.dirname(_os.path.dirname(_HERE2))
    _DEFAULT_DB_PATH2 = _os.path.join(_REPO_ROOT2, "data", "luna_ai_history.db")

    _CREATE_TABLE_SQL2 = """
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

    def _row_to_dict(row: _sqlite3.Row) -> dict:
        d = dict(row)
        for col in ("crater_ids", "weights", "ranked"):
            if d.get(col):
                try:
                    d[col] = _json.loads(d[col])
                except (_json.JSONDecodeError, TypeError):
                    pass
        return d

    class SQLiteAuditStore:
        def __init__(self, db_path: str = _DEFAULT_DB_PATH2) -> None:
            self._db_path = db_path

        def _connect(self) -> _sqlite3.Connection:
            _os.makedirs(_os.path.dirname(self._db_path), exist_ok=True)
            conn = _sqlite3.connect(self._db_path)
            conn.row_factory = _sqlite3.Row
            conn.execute(_CREATE_TABLE_SQL2)
            conn.commit()
            return conn

        def log_run(self, result: _Any, mode: str, weights_dict: dict) -> str:
            run_id = str(_uuid.uuid4())
            ts = _datetime.now(_timezone.utc).isoformat()
            ranked_list = []
            for i, rc in enumerate(result.ranked, start=1):
                ranked_list.append({
                    "rank": i,
                    "candidate_id": rc.candidate.candidate_id,
                    "total_score": round(rc.total_score, 6),
                })
            crater_ids = [rc.candidate.candidate_id for rc in result.ranked]
            for cid, _ in result.rejection_summary:
                if cid not in crater_ids:
                    crater_ids.append(cid)
            recommendation = result.ranked[0].candidate.candidate_id if result.ranked else None
            row = (
                run_id, ts, mode,
                _json.dumps(crater_ids), _json.dumps(weights_dict),
                result.total_candidates, result.passed_hc, result.rejected_hc,
                _json.dumps(ranked_list), recommendation,
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
