"""
RunState — persistent assessment state.

Layer 1: JSON file  run_state_{run_id}.json  (structured state)
Layer 2: SQLite     logs_{run_id}.db          (all subprocess log lines)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_loguru_line(line: str) -> tuple[str, str, str, str]:
    """
    Parse loguru format:
    '2026-03-25 16:49:04.395 | INFO     | cyberAI.recon.core:fn:42 - message'
    Returns (timestamp, level, module, message).
    """
    pattern = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s*\|\s*(\w+)\s*\|\s*([\w\.:<>]+)\s*-\s*(.*)$"
    m = re.match(pattern, line)
    if m:
        return m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
    return _utc_now(), "INFO", "unknown", line


# ---------------------------------------------------------------------------
# RunState
# ---------------------------------------------------------------------------

class RunState:
    """
    Persistent state for a single assessment run.

    JSON file : {output_dir}/{run_id}/run_state.json
    SQLite    : {output_dir}/{run_id}/logs.db
    """

    def __init__(self, run_id: str, target: str, output_dir: str = "outputs"):
        self.run_id = run_id
        self.target = target
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = run_dir / "run_state.json"
        self.db_file = run_dir / "logs.db"
        self._lock = threading.Lock()
        self._state = self._load_or_create()
        self._db_conn = self._init_db()

    # ------------------------------------------------------------------
    # init
    # ------------------------------------------------------------------

    def _load_or_create(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    data = json.load(f)
                # Always ensure target is set correctly (never example.com)
                data["target"] = self.target or data.get("target", "")
                return data
            except Exception:
                pass
        return {
            "run_id": self.run_id,
            "target": self.target,   # NEVER "example.com"
            "phase": "init",
            "sessions": {},
            "endpoints": [],
            "test_plan": [],
            "findings": [],
            "tested_endpoints": [],
            "errors": [],
            "phase_summaries": {},
            "created_at": _utc_now(),
        }

    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id    TEXT,
                phase     TEXT,
                level     TEXT,
                module    TEXT,
                message   TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        return conn

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        with self._lock:
            tmp = str(self.state_file) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            os.replace(tmp, str(self.state_file))

    # ------------------------------------------------------------------
    # generic get / set
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Supports dot-notation for nested keys: 'phase_summaries.recon.return_code'"""
        parts = key.split(".")
        d = self._state
        for part in parts[:-1]:
            if part not in d or not isinstance(d[part], dict):
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
        self.save()

    # ------------------------------------------------------------------
    # sessions
    # ------------------------------------------------------------------

    def add_session(self, name: str, session_data: dict) -> None:
        self._state["sessions"][name] = session_data
        self.save()

    def get_sessions(self) -> dict:
        return self._state.get("sessions", {})

    def get_session(self, name: str) -> Optional[dict]:
        return self._state.get("sessions", {}).get(name)

    # ------------------------------------------------------------------
    # endpoints
    # ------------------------------------------------------------------

    def add_endpoint(self, endpoint: dict) -> None:
        path = endpoint.get("path", "")
        existing = [e for e in self._state["endpoints"] if e.get("path") == path]
        if not existing:
            self._state["endpoints"].append(endpoint)
            self.save()

    def add_endpoints(self, endpoints: list[dict]) -> int:
        added = 0
        existing_paths = {e.get("path") for e in self._state["endpoints"]}
        for ep in endpoints:
            if ep.get("path") not in existing_paths:
                self._state["endpoints"].append(ep)
                existing_paths.add(ep.get("path"))
                added += 1
        if added:
            self.save()
        return added

    def get_endpoints(self) -> list[dict]:
        return self._state.get("endpoints", [])

    # ------------------------------------------------------------------
    # findings
    # ------------------------------------------------------------------

    def add_finding(self, finding: dict) -> str:
        """Auto-assigns finding_id if not present. Returns finding_id."""
        findings = self._state["findings"]
        if "id" not in finding:
            finding["id"] = f"F-{len(findings) + 1:03d}"
        finding.setdefault("discovered_at", _utc_now())
        findings.append(finding)
        self.save()
        return finding["id"]

    def update_finding(self, finding_id: str, updates: dict) -> bool:
        for f in self._state["findings"]:
            if f.get("id") == finding_id:
                f.update(updates)
                self.save()
                return True
        return False

    def get_findings(self, status: Optional[str] = None) -> list[dict]:
        findings = self._state.get("findings", [])
        if status:
            return [f for f in findings if f.get("status") == status]
        return findings

    def get_finding(self, finding_id: str) -> Optional[dict]:
        for f in self._state.get("findings", []):
            if f.get("id") == finding_id:
                return f
        return None

    # ------------------------------------------------------------------
    # test plan
    # ------------------------------------------------------------------

    def set_test_plan(self, plan: list[dict]) -> None:
        self._state["test_plan"] = plan
        self.save()

    def get_test_plan(self) -> list[dict]:
        return self._state.get("test_plan", [])

    def mark_endpoint_tested(self, path: str) -> None:
        if path not in self._state["tested_endpoints"]:
            self._state["tested_endpoints"].append(path)
            self.save()

    # ------------------------------------------------------------------
    # errors
    # ------------------------------------------------------------------

    def add_error(self, error: dict) -> None:
        error.setdefault("timestamp", _utc_now())
        self._state["errors"].append(error)
        self.save()

    # ------------------------------------------------------------------
    # phase management
    # ------------------------------------------------------------------

    def set_phase(self, phase: str) -> None:
        self._state["phase"] = phase
        self._state.setdefault("phase_summaries", {})[phase] = {
            "started_at": _utc_now()
        }
        self.save()

    def complete_phase(self, phase: str, summary: dict | None = None) -> None:
        ps = self._state.setdefault("phase_summaries", {}).setdefault(phase, {})
        ps["completed_at"] = _utc_now()
        if summary:
            ps.update(summary)
        self.save()

    # ------------------------------------------------------------------
    # SQLite log ingestion
    # ------------------------------------------------------------------

    def write_log(
        self,
        phase: str,
        level: str,
        module: str,
        message: str,
        timestamp: Optional[str] = None,
    ) -> None:
        ts = timestamp or _utc_now()
        with self._lock:
            self._db_conn.execute(
                "INSERT INTO logs (run_id, phase, level, module, message, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (self.run_id, phase, level.upper(), module, message, ts),
            )
            self._db_conn.commit()

    def write_log_line(self, phase: str, raw_line: str) -> None:
        """Parse a raw loguru line and write it to SQLite."""
        ts, level, module, message = _parse_loguru_line(raw_line)
        self.write_log(phase, level, module, message, ts)

    def query_logs(
        self,
        phase: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        last_n: int = 100,
    ) -> list[dict]:
        where: list[str] = ["run_id = ?"]
        params: list[Any] = [self.run_id]
        if phase:
            where.append("phase = ?")
            params.append(phase)
        if level:
            where.append("level = ?")
            params.append(level.upper())
        if search:
            where.append("message LIKE ?")
            params.append(f"%{search}%")
        sql = (
            f"SELECT timestamp, phase, level, module, message FROM logs "
            f"WHERE {' AND '.join(where)} "
            f"ORDER BY id DESC LIMIT ?"
        )
        params.append(last_n)
        rows = self._db_conn.execute(sql, params).fetchall()
        return [
            {"timestamp": r[0], "phase": r[1], "level": r[2], "module": r[3], "message": r[4]}
            for r in reversed(rows)
        ]

    def count_logs(self, phase: Optional[str] = None, level: Optional[str] = None) -> int:
        where = ["run_id = ?"]
        params: list[Any] = [self.run_id]
        if phase:
            where.append("phase = ?")
            params.append(phase)
        if level:
            where.append("level = ?")
            params.append(level.upper())
        row = self._db_conn.execute(
            f"SELECT COUNT(*) FROM logs WHERE {' AND '.join(where)}", params
        ).fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # summary helpers
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        findings = self._state.get("findings", [])
        return {
            "run_id": self.run_id,
            "target": self.target,
            "phase": self._state.get("phase"),
            "sessions_count": len(self._state.get("sessions", {})),
            "session_names": list(self._state.get("sessions", {}).keys()),
            "endpoints_count": len(self._state.get("endpoints", [])),
            "findings_count": len(findings),
            "findings_by_status": {
                "confirmed": len([f for f in findings if f.get("status") == "confirmed"]),
                "false_positive": len([f for f in findings if f.get("status") == "false_positive"]),
                "unverified": len([f for f in findings if f.get("status") == "unverified"]),
            },
            "test_plan_count": len(self._state.get("test_plan", [])),
            "errors_count": len(self._state.get("errors", [])),
        }

    def get_final_summary(self) -> dict:
        s = self.summary()
        s["findings"] = self._state.get("findings", [])
        s["phase_summaries"] = self._state.get("phase_summaries", {})
        return s

    def close(self) -> None:
        try:
            self._db_conn.close()
        except Exception:
            pass
