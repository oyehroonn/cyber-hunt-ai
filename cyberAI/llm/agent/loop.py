"""
CyberHunt AI V2 — Adaptive 50-turn agent loop.

Phase-aware: swaps system prompt on phase transitions.
Integrates RunState, InteractshManager, and all 20 tools.
"""

from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config


def _sync_to_result(value):
    """Wrap a synchronous return value in an awaitable coroutine."""
    async def _inner():
        return value
    return _inner()
from cyberAI.llm.agent.chat_client import chat_completion, extract_message
from cyberAI.llm.agent.prompts import get_phase_prompt
from cyberAI.llm.agent.state import RunState
from cyberAI.llm.agent.tool_definitions import ALL_TOOL_DEFINITIONS


# Phase completion heuristics — which tool calls signal end of a phase
_PHASE_COMPLETION_SIGNALS = {
    "recon": {"build_endpoint_inventory"},
    "plan": set(),  # Plan phase ends when agent says it's done
    "test": {"verify_finding"},
    "verify": {"verify_finding"},
    "report": {"write_report"},
}

_PHASE_ORDER = ["recon", "plan", "test", "verify", "report"]


def _next_phase(current: str) -> str:
    try:
        idx = _PHASE_ORDER.index(current)
        return _PHASE_ORDER[idx + 1] if idx + 1 < len(_PHASE_ORDER) else "report"
    except ValueError:
        return "plan"


def _detect_phase_from_tool(tool_name: str, current_phase: str) -> Optional[str]:
    """Return new phase if tool call signals phase completion."""
    if tool_name == "build_endpoint_inventory" and current_phase == "recon":
        return "plan"
    if tool_name == "write_report":
        return None  # Done
    return None


async def _dispatch_tool(
    name: str,
    args: dict,
    state: RunState,
    oob_manager,
    target_url: str,
    run_id: str,
) -> str:
    """Execute a tool by name and return JSON string result."""
    # Inject shared context into args
    args.setdefault("run_id", run_id)
    args.setdefault("target_url", target_url)

    try:
        from cyberAI.llm.agent.tools import (
            auth_register_and_login,
            crawl_target,
            analyze_js_bundles,
            fetch_api_schema,
            discover_endpoints,
            build_endpoint_inventory,
            analyze_security_headers,
            test_idor,
            test_ssrf_oob,
            test_auth_bypass,
            test_mass_assignment,
            test_race_condition,
            test_sqli_blind,
            replay_request_with_variants,
            diff_responses,
            verify_finding,
            store_finding,
            get_phase_logs,
            write_report,
            error_retry,
        )

        dispatch_map = {
            "auth_register_and_login": lambda: auth_register_and_login(
                target_url=args["target_url"],
                num_users=args.get("num_users", 2),
                also_try_admin=args.get("also_try_admin", True),
                run_id=args["run_id"],
                state=state,
            ),
            "crawl_target": lambda: crawl_target(
                target_url=args["target_url"],
                session_name=args.get("session_name"),
                max_pages=args.get("max_pages", 50),
                run_id=args["run_id"],
                state=state,
            ),
            "analyze_js_bundles": lambda: analyze_js_bundles(
                bundle_urls=args.get("bundle_urls", []),
                target_url=args["target_url"],
                run_id=args["run_id"],
                state=state,
            ),
            "fetch_api_schema": lambda: fetch_api_schema(
                target_url=args["target_url"],
                session_name=args.get("session_name"),
                run_id=args["run_id"],
                state=state,
            ),
            "discover_endpoints": lambda: discover_endpoints(
                target_url=args["target_url"],
                session_name=args.get("session_name"),
                concurrent_requests=args.get("concurrent_requests", 30),
                ai_extend=args.get("ai_extend", True),
                run_id=args["run_id"],
                state=state,
            ),
            "analyze_security_headers": lambda: analyze_security_headers(
                target_url=args["target_url"],
                sample_endpoints=args.get("sample_endpoints"),
                run_id=args["run_id"],
                state=state,
            ),
            "build_endpoint_inventory": lambda: build_endpoint_inventory(
                target_url=args["target_url"],
                run_id=args["run_id"],
                state=state,
            ),
            "test_idor": lambda: test_idor(
                endpoint=args["endpoint"],
                target_url=args["target_url"],
                run_id=args["run_id"],
                num_swaps=args.get("num_swaps", 10),
                test_vertical=args.get("test_vertical", True),
                state=state,
            ),
            "test_ssrf_oob": lambda: test_ssrf_oob(
                target_url=args["target_url"],
                injection_points=args.get("injection_points"),
                session_name=args.get("session_name", "user_a"),
                run_id=args["run_id"],
                state=state,
                oob_manager=oob_manager,
            ),
            "test_auth_bypass": lambda: test_auth_bypass(
                endpoints=args["endpoints"],
                target_url=args["target_url"],
                run_id=args["run_id"],
                state=state,
            ),
            "test_mass_assignment": lambda: test_mass_assignment(
                update_endpoints=args["update_endpoints"],
                target_url=args["target_url"],
                session_name=args.get("session_name", "user_a"),
                run_id=args["run_id"],
                state=state,
            ),
            "test_race_condition": lambda: test_race_condition(
                endpoint=args["endpoint"],
                payload=args.get("payload", {}),
                target_url=args["target_url"],
                num_concurrent=args.get("num_concurrent", 25),
                window_ms=args.get("window_ms", 50.0),
                session_name=args.get("session_name", "user_a"),
                run_id=args["run_id"],
                state=state,
            ),
            "test_sqli_blind": lambda: test_sqli_blind(
                endpoint=args["endpoint"],
                target_url=args["target_url"],
                session_name=args.get("session_name", "user_a"),
                run_id=args["run_id"],
                state=state,
            ),
            "replay_request_with_variants": lambda: replay_request_with_variants(
                base_request=args["base_request"],
                variants=args.get("variants", []),
                target_url=args["target_url"],
                run_id=args["run_id"],
                state=state,
            ),
            "diff_responses": lambda: _sync_to_result(diff_responses(
                response_a=args["response_a"],
                response_b=args["response_b"],
                context=args.get("context", "idor_check"),
            )),
            "verify_finding": lambda: verify_finding(
                finding_id=args["finding_id"],
                target_url=args["target_url"],
                run_id=args["run_id"],
                state=state,
                oob_manager=oob_manager,
            ),
            "store_finding": lambda: _sync_to_result(store_finding(
                finding_type=args["finding_type"],
                severity=args["severity"],
                title=args["title"],
                endpoint=args["endpoint"],
                method=args["method"],
                evidence=args["evidence"],
                cvss_score=args["cvss_score"],
                owasp_category=args["owasp_category"],
                cwe_id=args["cwe_id"],
                remediation=args["remediation"],
                target_url=args["target_url"],
                run_id=args["run_id"],
                state=state,
                subtype=args.get("subtype", ""),
                reproduction_steps=args.get("reproduction_steps"),
            )),
            "get_phase_logs": lambda: _sync_to_result(get_phase_logs(
                run_id=args["run_id"],
                phase=args.get("phase"),
                level=args.get("level"),
                search=args.get("search"),
                last_n=args.get("last_n", 100),
                state=state,
            )),
            "write_report": lambda: write_report(
                run_id=args["run_id"],
                target_url=args["target_url"],
                formats=args.get("formats", ["markdown", "json", "csv"]),
                include_raw_evidence=args.get("include_raw_evidence", True),
                executive_summary=args.get("executive_summary", True),
                state=state,
                output_dir=str(get_config().output_dir),
            ),
            "error_retry": lambda: error_retry(
                failed_tool=args["failed_tool"],
                error=args["error"],
                original_args=args.get("original_args", {}),
                run_id=args["run_id"],
                state=state,
                attempt=args.get("attempt", 1),
            ),
        }

        handler = dispatch_map.get(name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {name}"})

        # Handle sync vs async
        result = handler()
        if asyncio.iscoroutine(result):
            result = await result

        # diff_responses and store_finding and get_phase_logs are sync — wrap result
        if not isinstance(result, (dict, list)):
            result = {"result": result}

        return json.dumps(result, default=str)[:120000]

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Tool {name} raised exception: {e}\n{tb[:500]}")
        state.write_log("test", "ERROR", f"tool.{name}", f"{type(e).__name__}: {str(e)[:200]}")
        return json.dumps({"error": f"{type(e).__name__}: {str(e)[:200]}", "tool": name})


async def run_agent_loop(
    run_id: str,
    target_url: str,
    goal: str = "",
    max_turns: Optional[int] = None,
    log_tail_lines: Optional[int] = None,
    output_dir: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run the CyberHunt AI V2 adaptive 50-turn agent loop.

    - Phase-aware system prompt swapping
    - Integrates RunState (JSON + SQLite persistence)
    - Integrates InteractshManager for OOB SSRF
    - Dispatches all 20 tools
    - Returns final assessment summary

    Returns:
    {
      "status": "finished" | "max_turns" | "error",
      "turns": 34,
      "run_id": "abc123",
      "findings_count": 7,
      "final_summary": {...}
    }
    """
    cfg = get_config()
    max_turns = max_turns if max_turns is not None else getattr(cfg, "agent_max_turns", 50)
    output_dir = output_dir or str(cfg.output_dir)

    # Initialize persistent state
    state = RunState(run_id=run_id, target=target_url, output_dir=output_dir)
    state.write_log("test", "INFO", "loop", f"Agent loop started: target={target_url} max_turns={max_turns}")

    # Start Interactsh OOB manager
    oob_manager = None
    try:
        from cyberAI.infra.oob import InteractshManager
        oob_manager = InteractshManager()
        await oob_manager.start()
        logger.info("InteractshManager started successfully")
    except Exception as e:
        logger.warning(f"InteractshManager unavailable (non-fatal): {e}")
        oob_manager = None

    current_phase = "recon"
    system_prompt = get_phase_prompt(current_phase)

    state_summary = state.summary()
    initial_user = (
        f"Assessment Run ID: {run_id}\n"
        f"Target: {target_url}\n"
        f"Current state summary: {json.dumps(state_summary, indent=2)}\n\n"
        f"Begin the security assessment. Your first tool call MUST be auth_register_and_login.\n"
        f"Do NOT skip any phase. Follow the mandatory tool call sequence in the system prompt.\n"
        + (f"\nGoal: {goal}" if goal else "")
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": f"{system_prompt}\n\nTARGET_URL={target_url}\nRUN_ID={run_id}",
        },
        {"role": "user", "content": initial_user},
    ]

    finished = False
    finish_reason = ""

    for turn in range(max_turns):
        logger.info(f"Agent loop turn {turn + 1}/{max_turns} (phase={current_phase})")

        # Call LLM
        try:
            resp = await asyncio.to_thread(
                chat_completion,
                messages,
                tools=ALL_TOOL_DEFINITIONS,
                temperature=0.2,
            )
        except Exception as e:
            logger.error(f"chat_completion failed on turn {turn + 1}: {e}")
            state.write_log("test", "ERROR", "loop", f"LLM call failed: {str(e)[:200]}")
            # Check if we should switch to Ollama
            if "402" in str(e) or "Payment Required" in str(e):
                logger.warning("OpenRouter 402 — attempting Ollama fallback")
                try:
                    resp = await asyncio.to_thread(
                        chat_completion,
                        messages,
                        tools=ALL_TOOL_DEFINITIONS,
                        temperature=0.2,
                        use_ollama=True,
                    )
                except Exception as e2:
                    logger.error(f"Ollama fallback also failed: {e2}")
                    return {"status": "error", "error": str(e2), "turns": turn, "run_id": run_id}
            else:
                return {"status": "error", "error": str(e), "turns": turn, "run_id": run_id}

        msg = extract_message(resp)
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls")

        # No tool calls — prompt the agent to act
        if not tool_calls:
            if content and "__FINISH__" in content:
                finish_reason = content
                finished = True
                break

            messages.append({"role": "assistant", "content": content or ""})
            messages.append({
                "role": "user",
                "content": (
                    f"You are in phase '{current_phase}'. You did not call a tool. "
                    "You must use tools to make progress. "
                    "If you have completed this phase, call build_endpoint_inventory (recon), "
                    "or write_report (report). If assessment is complete, include __FINISH__ "
                    "in your response with a summary."
                ),
            })
            continue

        # Build assistant message
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        }
        messages.append(assistant_msg)

        # Execute all tool calls
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            raw_args = fn.get("arguments") or "{}"
            tid = tc.get("id", "call_unknown")

            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                args = {}

            if not isinstance(args, dict):
                args = {}

            logger.debug(f"Executing tool: {name}")
            result_str = await _dispatch_tool(
                name=name,
                args=args,
                state=state,
                oob_manager=oob_manager,
                target_url=target_url,
                run_id=run_id,
            )

            messages.append({
                "role": "tool",
                "tool_call_id": tid,
                "content": result_str,
            })

            # Phase transition detection
            new_phase = _detect_phase_from_tool(name, current_phase)
            if new_phase and new_phase != current_phase:
                logger.info(f"Phase transition: {current_phase} → {new_phase}")
                current_phase = new_phase
                state.set("phase", current_phase)
                state.write_log("test", "INFO", "loop", f"Phase transition → {current_phase}")
                # Inject new phase prompt
                messages[0] = {
                    "role": "system",
                    "content": f"{get_phase_prompt(current_phase)}\n\nTARGET_URL={target_url}\nRUN_ID={run_id}",
                }

            # Check for write_report completion
            if name == "write_report":
                try:
                    result_data = json.loads(result_str)
                    if result_data.get("reports_written"):
                        finished = True
                        finish_reason = f"__FINISH__ Report written: {result_data['reports_written']}"
                except Exception:
                    pass

        if finished:
            break

    # Cleanup
    if oob_manager:
        try:
            await oob_manager.stop()
        except Exception:
            pass

    state.write_log("test", "INFO", "loop",
                    f"Loop ended: turns={turn + 1} finished={finished}")

    final_summary = state.get_final_summary()

    return {
        "status": "finished" if finished else "max_turns",
        "reason": finish_reason,
        "turns": turn + 1,
        "run_id": run_id,
        "findings_count": len(state.get_findings()),
        "final_summary": final_summary,
    }
