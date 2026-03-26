"""
LLM assessment orchestrator: phase events, structured context, guidance, final Markdown report.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.llm.engagement_context import build_engagement_context, context_to_prompt_chunk
from cyberAI.utils.helpers import atomic_write_json


def _call_llm(prompt: str, context_chunks: list[str]) -> str:
    from cyberAI.llm.llm_client import call_llm

    return call_llm(prompt, context=context_chunks)


class LLMAssessmentOrchestrator:
    """
    Records phase outcomes and produces LLM guidance + final report.
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.config = get_config()
        out = self.config.get_output_path("llm", "engagement")
        out.mkdir(parents=True, exist_ok=True)
        self._log_path = out / f"events_{run_id}.jsonl"
        self._events: list[dict[str, Any]] = []

    def append_event(self, phase: str, event: str, data: Optional[dict[str, Any]] = None) -> None:
        row = {
            "ts": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "phase": phase,
            "event": event,
            "data": data or {},
        }
        self._events.append(row)
        line = json.dumps(row, default=str, ensure_ascii=False) + "\n"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def build_full_context(self, phase: str = "report", extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        base = build_engagement_context(self.run_id, phase=phase, extra=extra)
        base["orchestrator_events"] = self._events[-40:]
        return base

    def phase_guidance(self, phase_completed: str, phase_summary: Optional[dict[str, Any]] = None) -> str:
        """LLM: next-step guidance after a phase completes."""
        if not self.config.llm_enabled or not self.config.llm_orchestration_enabled:
            return ""
        ctx = self.build_full_context(phase=phase_completed, extra={"last_phase_summary": phase_summary})
        chunk = context_to_prompt_chunk(ctx, max_chars=14000)
        prompt = f"""You are the security assessment orchestrator for an automated pipeline (recon → plan → test → verify → report).

The assessment run is for ANY web target; do not assume OWASP Juice Shop.

Phase just completed: {phase_completed}

Your tasks:
1. Briefly summarize what this phase produced (2–4 sentences).
2. List concrete next actions for the operator OR for the automation (bullet list).
3. Mention which CLI commands or test categories are most useful next (e.g. confirmed_authz, ssrf_oob, rag).
4. If ROLE_ACCOUNTS / OOB webhook are missing, say what to configure in .env.

Respond in Markdown with headings ## Summary, ## Next steps, ## Configuration hints.
"""
        try:
            return _call_llm(prompt, [chunk])
        except Exception as e:
            logger.warning(f"LLM orchestration guidance failed: {e}")
            return f"[LLM guidance unavailable: {e}]"

    async def phase_guidance_async(self, phase_completed: str, phase_summary: Optional[dict[str, Any]] = None) -> str:
        import asyncio

        return await asyncio.to_thread(self.phase_guidance, phase_completed, phase_summary)

    def final_markdown_report(self) -> str:
        """LLM: full assessment report from entire run context."""
        if not self.config.llm_enabled:
            return ""
        ctx = self.build_full_context(phase="report")
        chunk = context_to_prompt_chunk(ctx, max_chars=20000)
        prompt = f"""You are writing the final security assessment report for an automated engagement.

Rules:
- The target is generic; describe findings by behavior (authorization, SSRF, injection, etc.), not by CTF name.
- Separate **confirmed** evidence (OOB callback, differential sessions, unauthenticated access to sensitive APIs) from **heuristic / needs triage** (RAG-only signals).
- Include Executive summary, Methodology, Findings overview, Risk summary, Recommendations, Limitations.
- Use professional Markdown (tables allowed).

Respond with complete Markdown only, no preamble.
"""
        try:
            return _call_llm(prompt, [chunk])
        except Exception as e:
            logger.warning(f"LLM final report failed: {e}")
            return f"# Report\n\nLLM generation failed: {e}"

    async def final_markdown_report_async(self) -> str:
        import asyncio

        return await asyncio.to_thread(self.final_markdown_report)

    def save_final_report(self, markdown: str) -> Path:
        path = self.config.get_output_path("reports", "markdown", f"llm_assessment_report_{self.run_id}.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        meta = {
            "_meta": {
                "generated_at": datetime.utcnow().isoformat(),
                "run_id": self.run_id,
                "target_url": self.config.target_url,
                "phase": "llm_report",
            },
            "markdown_path": str(path),
        }
        atomic_write_json(self.config.get_output_path("llm", "engagement", f"report_meta_{self.run_id}.json"), meta)
        return path


_orchestrator: Optional[LLMAssessmentOrchestrator] = None


def get_orchestrator(run_id: str) -> LLMAssessmentOrchestrator:
    global _orchestrator
    if _orchestrator is None or _orchestrator.run_id != run_id:
        _orchestrator = LLMAssessmentOrchestrator(run_id)
    return _orchestrator


def reset_orchestrator() -> None:
    global _orchestrator
    _orchestrator = None
