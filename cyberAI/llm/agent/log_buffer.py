"""Read recent lines from CyberAI log files for a given run_id."""

from __future__ import annotations

from pathlib import Path

from cyberAI.config import get_config


def tail_logs_for_run(run_id: str, max_lines: int = 80, max_chars: int = 24000) -> str:
    """
    Concatenate last ``max_lines`` lines from log files under outputs/logs/
    whose name contains ``run_id``.
    """
    cfg = get_config()
    log_dir = cfg.get_output_path("logs")
    if not log_dir.is_dir():
        return f"[no log dir: {log_dir}]"

    chunks: list[str] = []
    for path in sorted(log_dir.glob("*.log")):
        if run_id not in path.name:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            tail = lines[-max_lines:]
            chunks.append(f"--- {path.name} (last {len(tail)} lines) ---\n" + "\n".join(tail))
        except OSError as e:
            chunks.append(f"--- {path.name} [read error: {e}] ---")

    if not chunks:
        return f"[no log files matched run_id={run_id} in {log_dir}]"

    out = "\n\n".join(chunks)
    if len(out) > max_chars:
        return out[-max_chars:]
    return out
