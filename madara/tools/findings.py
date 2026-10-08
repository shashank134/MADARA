"""Findings store — durable state that survives restarts and model swaps.
Bug bounty is long-horizon; the agent must be able to resume. This is a thin
sqlite store the agent writes confirmed findings / tested endpoints / leads to.
"""
from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

DB_DEFAULT = Path(__file__).resolve().parent.parent.parent / "findings" / "state.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program TEXT, title TEXT, severity TEXT, status TEXT,
    target TEXT, detail TEXT, evidence_path TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS tested (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program TEXT, endpoint TEXT, note TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program TEXT, lead TEXT, status TEXT DEFAULT 'open', created_at REAL
);
CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program TEXT, report_id TEXT,
    verdict TEXT,          -- positive|false|overclaim|theoretical|incomplete
    confidence REAL,
    claimed_impact TEXT, demonstrated_impact TEXT,
    claimed_severity TEXT, assessed_severity TEXT,
    detail TEXT,           -- JSON: evidence, missing_info, rationale, etc.
    created_at REAL
);
"""


class Findings:
    name = "record_finding"
    description = "Persist a confirmed finding, a tested endpoint, or an open lead."
    input_schema = {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["finding", "tested", "lead", "verdict"]},
            "data": {"type": "object"},
        },
        "required": ["kind", "data"],
        "additionalProperties": False,
    }

    def __init__(self, program: str, db_path: Path | None = None):
        self.program = program
        self.db = sqlite3.connect(str(db_path or DB_DEFAULT))
        self.db.executescript(_SCHEMA)
        self.db.commit()

    def run(self, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        now = time.time()
        if kind == "finding":
            self.db.execute(
                "INSERT INTO findings(program,title,severity,status,target,detail,evidence_path,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (self.program, data.get("title"), data.get("severity"),
                 data.get("status", "unverified"), data.get("target"),
                 json.dumps(data.get("detail")), data.get("evidence_path"), now))
        elif kind == "tested":
            self.db.execute(
                "INSERT INTO tested(program,endpoint,note,created_at) VALUES(?,?,?,?)",
                (self.program, data.get("endpoint"), data.get("note"), now))
        elif kind == "lead":
            self.db.execute(
                "INSERT INTO leads(program,lead,status,created_at) VALUES(?,?,?,?)",
                (self.program, data.get("lead"), data.get("status", "open"), now))
        elif kind == "verdict":
            # A verify-poc / verify-report result. `detail` holds the full JSON
            # (evidence, missing_info, rationale, what_would_change_verdict…).
            known = {"report_id", "verdict", "confidence", "claimed_impact",
                     "demonstrated_impact", "claimed_severity", "assessed_severity"}
            self.db.execute(
                "INSERT INTO verdicts(program,report_id,verdict,confidence,claimed_impact,"
                "demonstrated_impact,claimed_severity,assessed_severity,detail,created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                (self.program, data.get("report_id"), data.get("verdict"),
                 data.get("confidence"), data.get("claimed_impact"),
                 data.get("demonstrated_impact"), data.get("claimed_severity"),
                 data.get("assessed_severity"),
                 json.dumps({k: v for k, v in data.items() if k not in known}), now))
        else:
            return {"error": "unknown_kind"}
        self.db.commit()
        return {"ok": True, "kind": kind}

    def summary(self) -> dict[str, Any]:
        cur = self.db.cursor()
        out = {}
        for t in ("findings", "tested", "leads", "verdicts"):
            cur.execute(f"SELECT COUNT(*) FROM {t} WHERE program=?", (self.program,))
            out[t] = cur.fetchone()[0]
        return out
