"""Local SQLite storage for check runs and their findings."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from .validation import Finding

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    input_path TEXT NOT NULL,
    contract_name TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    finding_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    check_name TEXT NOT NULL,
    message TEXT NOT NULL,
    row INTEGER,
    field TEXT
);
CREATE INDEX IF NOT EXISTS findings_by_run ON findings(run_id, position);
"""


@dataclass(frozen=True)
class RunInfo:
    """Metadata of a stored run."""

    id: int
    created_at: str
    input_path: str
    contract_name: str
    contract_version: str
    record_count: int
    finding_count: int


class RunStore:
    """Persists run metadata and findings in a SQLite database (`:memory:` allowed)."""

    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "RunStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def save_run(
        self,
        input_path: str,
        contract_name: str,
        contract_version: str,
        record_count: int,
        findings: Iterable[Finding],
        created_at: str | None = None,
    ) -> int:
        """Store a run with its findings (in the given order) and return the run id."""
        items = list(findings)
        stamp = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO runs (created_at, input_path, contract_name, contract_version,"
                " record_count, finding_count) VALUES (?, ?, ?, ?, ?, ?)",
                (stamp, str(input_path), contract_name, str(contract_version),
                 record_count, len(items)),
            )
            run_id = int(cursor.lastrowid)
            self._conn.executemany(
                "INSERT INTO findings (run_id, position, check_name, message, row, field)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (run_id, index, f.check, f.message, f.row, f.field)
                    for index, f in enumerate(items)
                ],
            )
        return run_id

    def get_run(self, run_id: int) -> RunInfo | None:
        row = self._conn.execute(
            "SELECT id, created_at, input_path, contract_name, contract_version,"
            " record_count, finding_count FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        return RunInfo(*row) if row else None

    def list_runs(self) -> list[RunInfo]:
        rows = self._conn.execute(
            "SELECT id, created_at, input_path, contract_name, contract_version,"
            " record_count, finding_count FROM runs ORDER BY id"
        ).fetchall()
        return [RunInfo(*row) for row in rows]

    def get_findings(self, run_id: int) -> list[Finding]:
        rows = self._conn.execute(
            "SELECT check_name, message, row, field FROM findings"
            " WHERE run_id = ? ORDER BY position",
            (run_id,),
        ).fetchall()
        return [Finding(check=c, message=m, row=r, field=f) for c, m, r, f in rows]
