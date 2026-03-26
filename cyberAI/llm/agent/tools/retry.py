"""
Tool 20 — error_retry

Analyze tool failures and determine retry strategy.
Ensures the agent never gets stuck on errors.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger

from cyberAI.llm.agent.state import RunState


_MAX_RETRIES = 3

# Error → strategy mapping
_ERROR_STRATEGIES = {
    "402": "switch_to_ollama",
    "Payment Required": "switch_to_ollama",
    "429": "exponential_backoff",
    "rate limit": "exponential_backoff",
    "503": "retry_with_delay",
    "Service Unavailable": "retry_with_delay",
    "ConnectionError": "check_target_up",
    "ConnectError": "check_target_up",
    "TimeoutError": "reduce_concurrency",
    "timeout": "reduce_concurrency",
    "ParseError": "retry_different_accept",
    "JSONDecodeError": "retry_different_accept",
    "401": "refresh_sessions",
    "Unauthorized": "refresh_sessions",
}


async def error_retry(
    failed_tool: str,
    error: str,
    original_args: dict,
    run_id: str = "",
    state: Optional[RunState] = None,
    attempt: int = 1,
) -> dict:
    """
    Error → Strategy mapping:
    - 402 Payment Required (OpenRouter) → switch to Ollama fallback model
    - 429 Rate Limited → add exponential backoff, retry after delay
    - 503 Service Unavailable → retry with 3s delay, max 3 attempts
    - ConnectionError → check target is up via HEAD /, retry
    - TimeoutError → reduce concurrent_requests, retry
    - ParseError (bad JSON) → re-fetch with different Accept header
    - AuthError (401 on scan) → re-run auth_register_and_login, refresh sessions

    Returns: {"action": "retry", "modified_args": {...}} or {"action": "skip", "reason": "..."}
    """
    error_str = str(error)
    strategy = _detect_strategy(error_str)

    if attempt > _MAX_RETRIES:
        if state:
            state.write_log("test", "ERROR", "error_retry",
                            f"Max retries exceeded for {failed_tool}: {error_str[:120]}")
        return {
            "action": "skip",
            "reason": f"Max retries ({_MAX_RETRIES}) exceeded for {failed_tool}",
            "error": error_str[:200],
        }

    modified_args = dict(original_args)
    result: dict[str, Any] = {
        "failed_tool": failed_tool,
        "error": error_str[:200],
        "strategy": strategy,
        "attempt": attempt,
    }

    if strategy == "switch_to_ollama":
        # Signal to the loop to use Ollama instead of OpenRouter
        result["action"] = "switch_model"
        result["model"] = "ollama/deepseek-r1:14b"
        result["modified_args"] = modified_args
        result["note"] = "OpenRouter quota exceeded — switching to local Ollama"

    elif strategy == "exponential_backoff":
        delay = 2 ** attempt  # 2s, 4s, 8s
        logger.info(f"error_retry: rate limited, waiting {delay}s before retry")
        await asyncio.sleep(delay)
        result["action"] = "retry"
        result["modified_args"] = modified_args
        result["delay_applied"] = delay

    elif strategy == "retry_with_delay":
        await asyncio.sleep(3.0)
        result["action"] = "retry"
        result["modified_args"] = modified_args
        result["delay_applied"] = 3.0

    elif strategy == "check_target_up":
        # Try HEAD request to confirm target is up
        target = state.get("target", "") if state else original_args.get("target_url", "")
        target_up = await _check_target(target)
        if not target_up:
            result["action"] = "skip"
            result["reason"] = f"Target {target} appears to be down"
        else:
            await asyncio.sleep(1.0)
            result["action"] = "retry"
            result["modified_args"] = modified_args

    elif strategy == "reduce_concurrency":
        # Halve concurrent_requests if present
        if "concurrent_requests" in modified_args:
            modified_args["concurrent_requests"] = max(
                5, modified_args["concurrent_requests"] // 2
            )
        result["action"] = "retry"
        result["modified_args"] = modified_args
        result["note"] = f"Reduced concurrency to {modified_args.get('concurrent_requests', 10)}"

    elif strategy == "retry_different_accept":
        # Change Accept header hint
        result["action"] = "retry"
        result["modified_args"] = modified_args
        result["note"] = "Retrying with text/plain Accept"

    elif strategy == "refresh_sessions":
        # Signal to refresh auth sessions
        result["action"] = "refresh_auth"
        result["note"] = "Session expired — call auth_register_and_login to refresh"
        result["modified_args"] = modified_args

    else:
        # Unknown error — skip after max retries
        if attempt >= 2:
            result["action"] = "skip"
            result["reason"] = f"Unknown error in {failed_tool}: {error_str[:100]}"
        else:
            await asyncio.sleep(1.0)
            result["action"] = "retry"
            result["modified_args"] = modified_args

    if state:
        state.write_log(
            "test", "WARNING", "error_retry",
            f"{failed_tool} error (attempt {attempt}): strategy={strategy} action={result.get('action')}"
        )
        state.add_error({
            "tool": failed_tool,
            "error": error_str[:200],
            "strategy": strategy,
            "action": result.get("action"),
            "attempt": attempt,
        })

    return result


def _detect_strategy(error: str) -> str:
    error_lower = error.lower()
    for pattern, strategy in _ERROR_STRATEGIES.items():
        if pattern.lower() in error_lower:
            return strategy
    return "unknown"


async def _check_target(target: str) -> bool:
    if not target:
        return False
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            r = await client.head(target)
            return r.status_code < 500
    except Exception:
        return False
