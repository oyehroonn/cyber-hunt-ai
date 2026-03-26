"""Persistent episodic + scratchpad memory for the assessment agent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from cyberAI.config import get_config


class AgentMemoryStore:
    """Append-only notes + full transcript path."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        cfg = get_config()
        self._base = cfg.get_output_path("llm", "agent_memory")
        self._base.mkdir(parents=True, exist_ok=True)
        self._scratch_path = self._base / f"scratch_{run_id}.jsonl"
        self._transcript_path = self._base / f"transcript_{run_id}.jsonl"

    def append_scratch(self, kind: str, text: str, extra: Optional[dict[str, Any]] = None) -> None:
        row = {
            "ts": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "kind": kind,
            "text": text[:8000],
            **(extra or {}),
        }
        with open(self._scratch_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def load_scratch_summary(self, max_lines: int = 40) -> str:
        if not self._scratch_path.is_file():
            return ""
        lines = self._scratch_path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-max_lines:]
        return "\n".join(tail)

    def append_transcript(self, record: dict[str, Any]) -> None:
        record = {**record, "ts": datetime.utcnow().isoformat(), "run_id": self.run_id}
        with open(self._transcript_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
