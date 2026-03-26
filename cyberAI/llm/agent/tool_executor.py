"""Allowlisted tool implementations for the assessment agent."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger

from cyberAI.config import get_config
from cyberAI.llm.agent.log_buffer import tail_logs_for_run
from cyberAI.llm.agent.memory_store import AgentMemoryStore


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


ALLOWED_PHASES = frozenset({"recon", "plan", "test", "verify", "report"})

# OpenAI-style tool definitions for /v1/chat/completions
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_pipeline_phase",
            "description": (
                "Run one CyberAI pipeline phase via the official CLI (subprocess). "
                "Use recon first, then plan, test, verify, report. "
                "Do not run destructive commands outside this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": list(ALLOWED_PHASES),
                    },
                    "categories": {
                        "type": "string",
                        "description": "Optional for test phase only, e.g. rag,confirmed_authz,ssrf_oob,authz",
                    },
                },
                "required": ["phase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_artifact",
            "description": "Read a UTF-8 text or JSON file under the assessment output directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Path relative to OUTPUT_DIR, e.g. recon/intelligence/master_intel.json",
                    },
                    "max_chars": {"type": "integer", "default": 32000},
                },
                "required": ["relative_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_artifacts",
            "description": "List files under a subdirectory of OUTPUT_DIR (non-recursive or shallow).",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Subdir under outputs, e.g. testing/findings",
                    },
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["subpath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_logs",
            "description": "Return recent log lines for this run_id from outputs/logs/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_lines": {"type": "integer", "default": 80},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "http_probe",
            "description": "HTTP GET or HEAD to the target application only (same host as TARGET_URL).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path_or_url": {
                        "type": "string",
                        "description": "Full URL or path starting with /",
                    },
                    "method": {"type": "string", "enum": ["GET", "HEAD"], "default": "GET"},
                },
                "required": ["path_or_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_save",
            "description": "Persist a short note (hypothesis, error summary, finding) for later turns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "description": "e.g. hypothesis, error, note, finding",
                    },
                    "text": {"type": "string"},
                },
                "required": ["kind", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_load",
            "description": "Load recent saved memory lines for this run.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "End the agent loop when assessment goals are met or blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                },
                "required": ["reason"],
            },
        },
    },
]


class AgentToolExecutor:
    def __init__(self, run_id: str, target_url: str):
        self.run_id = run_id
        self.target_url = (target_url or "").rstrip("/")
        self.config = get_config()
        self._memory = AgentMemoryStore(run_id)

    def _safe_output_path(self, relative: str) -> Path:
        base = self.config.output_dir.resolve()
        rel = (relative or ".").strip().replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            raise ValueError("path traversal denied")
        p = (base / rel).resolve()
        if not str(p).startswith(str(base)):
            raise ValueError("path outside OUTPUT_DIR")
        return p

    async def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        try:
            if name == "run_pipeline_phase":
                return await self._run_pipeline_phase(
                    str(arguments.get("phase", "")),
                    categories=arguments.get("categories"),
                )
            if name == "read_artifact":
                return self._read_artifact(
                    str(arguments.get("relative_path", "")),
                    int(arguments.get("max_chars") or 32000),
                )
            if name == "list_artifacts":
                return self._list_artifacts(
                    str(arguments.get("subpath", "")),
                    int(arguments.get("limit") or 50),
                )
            if name == "get_recent_logs":
                return tail_logs_for_run(
                    self.run_id,
                    max_lines=int(arguments.get("max_lines") or 80),
                )
            if name == "http_probe":
                return await self._http_probe(
                    str(arguments.get("path_or_url", "")),
                    str(arguments.get("method") or "GET").upper(),
                )
            if name == "memory_save":
                return self._memory_save(
                    str(arguments.get("kind", "note")),
                    str(arguments.get("text", "")),
                )
            if name == "memory_load":
                return self._memory.load_scratch_summary()
            if name == "finish":
                return "__FINISH__:" + str(arguments.get("reason", "done"))
            return f"unknown tool: {name}"
        except Exception as e:
            logger.exception("tool dispatch")
            return f"TOOL_ERROR {name}: {e}"

    async def _run_pipeline_phase(
        self,
        phase: str,
        categories: Optional[str] = None,
    ) -> str:
        if phase not in ALLOWED_PHASES:
            return f"error: phase must be one of {sorted(ALLOWED_PHASES)}"
        root = _repo_root()
        cmd = [sys.executable, "-m", "cyberAI.main", phase, "--run-id", self.run_id]
        if phase == "recon":
            if not self.target_url:
                return "error: TARGET_URL required for recon"
            cmd += ["--target", self.target_url]
        elif phase == "test":
            if self.target_url:
                cmd += ["--target", self.target_url]
            if categories:
                cmd += ["--categories", categories]
        timeout = 900.0 if phase == "recon" else 600.0
        logger.info(f"agent subprocess: {' '.join(cmd)} (cwd={root})")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ.copy(),
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"error: timeout after {timeout}s for phase={phase}"
        text = out.decode(errors="replace")
        if len(text) > 25000:
            text = text[-25000:] + "\n... [truncated]"
        return f"exit={proc.returncode}\n{text}"

    def _read_artifact(self, relative_path: str, max_chars: int) -> str:
        p = self._safe_output_path(relative_path)
        if not p.is_file():
            return f"error: not a file: {relative_path}"
        data = p.read_text(encoding="utf-8", errors="replace")
        if len(data) > max_chars:
            return data[:max_chars] + "\n... [truncated]"
        return data

    def _list_artifacts(self, subpath: str, limit: int) -> str:
        d = self._safe_output_path(subpath)
        if not d.is_dir():
            return f"error: not a directory: {subpath}"
        names = sorted(d.iterdir())[:limit]
        lines = [x.name + ("/" if x.is_dir() else "") for x in names]
        return "\n".join(lines) or "(empty)"

    async def _http_probe(self, path_or_url: str, method: str) -> str:
        if not self.target_url:
            return "error: no TARGET_URL"
        target = urlparse(self.target_url)
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            u = urlparse(path_or_url)
            if u.netloc.lower() != target.netloc.lower():
                return f"error: host not allowed (must be {target.netloc})"
            url = path_or_url
        else:
            path = path_or_url if path_or_url.startswith("/") else "/" + path_or_url
            url = f"{self.target_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                if method == "HEAD":
                    r = await client.head(url, follow_redirects=False)
                else:
                    r = await client.get(url, follow_redirects=False)
                body = (r.text or "")[:4000]
                return f"status={r.status_code}\nheaders={dict(r.headers)}\nbody_preview=\n{body}"
        except Exception as e:
            return f"http_probe error: {e}"

    def _memory_save(self, kind: str, text: str) -> str:
        self._memory.append_scratch(kind, text)
        return f"saved memory kind={kind} ({len(text)} chars)"
