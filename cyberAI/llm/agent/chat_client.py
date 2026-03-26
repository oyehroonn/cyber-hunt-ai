"""
OpenAI-compatible chat completions with Ollama fallback.

Fallback hierarchy:
1. Primary: OpenRouter (OPENROUTER_API_KEY) or DeepSeek (DEEPSEEK_API_KEY)
2. Fallback: Local Ollama (http://localhost:11434) on 402/429 errors
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import httpx

from cyberAI.llm.project_env import get_openai_compatible_llm_config, load_project_dotenv


_OLLAMA_BASE_URL = "http://localhost:11434"
_OLLAMA_MODEL = "deepseek-r1:14b"
_MAX_RETRIES = 3


def chat_completion(
    messages: list[dict[str, Any]],
    tools: Optional[list[dict[str, Any]]] = None,
    temperature: float = 0.2,
    max_tokens: int = 8192,
    use_ollama: bool = False,
) -> dict[str, Any]:
    """
    POST /v1/chat/completions. Returns full JSON response dict.

    Automatically falls back to Ollama on 402 (quota exceeded) or persistent 429.
    """
    load_project_dotenv()
    cfg = get_openai_compatible_llm_config()

    if use_ollama or not cfg.api_key:
        return _ollama_chat(messages, tools, temperature, max_tokens)

    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    headers.update(cfg.extra_headers)

    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            with httpx.Client(timeout=300.0) as client:
                r = client.post(
                    f"{cfg.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

                # 402: quota exceeded → switch to Ollama
                if r.status_code == 402:
                    raise RuntimeError(f"402 Payment Required — OpenRouter quota exceeded")

                # 429: rate limit → exponential backoff
                if r.status_code == 429:
                    delay = 2 ** (attempt + 1)
                    time.sleep(delay)
                    last_error = f"429 Rate Limited (attempt {attempt + 1})"
                    continue

                # Some providers reject unknown params — retry without tools once
                if r.status_code in (400, 422) and tools:
                    payload.pop("tools", None)
                    payload.pop("tool_choice", None)
                    r = client.post(
                        f"{cfg.base_url}/v1/chat/completions",
                        json=payload,
                        headers=headers,
                    )

                r.raise_for_status()
                return r.json()

        except RuntimeError:
            raise
        except Exception as e:
            last_error = str(e)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(1.0)
            continue

    raise RuntimeError(f"chat_completion failed after {_MAX_RETRIES} attempts: {last_error}")


def _ollama_chat(
    messages: list[dict[str, Any]],
    tools: Optional[list[dict[str, Any]]],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    """
    Call local Ollama instance at http://localhost:11434.
    Returns OpenAI-compatible response format.
    """
    payload: dict[str, Any] = {
        "model": _OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if tools:
        # Ollama supports tools in newer versions
        payload["tools"] = tools

    with httpx.Client(timeout=300.0) as client:
        r = client.post(f"{_OLLAMA_BASE_URL}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()

    # Normalize to OpenAI format
    message = data.get("message", {})
    return {
        "choices": [
            {
                "message": {
                    "role": message.get("role", "assistant"),
                    "content": message.get("content", ""),
                    "tool_calls": message.get("tool_calls"),
                },
                "finish_reason": "stop" if not message.get("tool_calls") else "tool_calls",
            }
        ],
        "model": _OLLAMA_MODEL,
        "usage": data.get("usage", {}),
    }


def extract_message(resp: dict[str, Any]) -> dict[str, Any]:
    """Return the first choice message dict."""
    choices = resp.get("choices") or []
    if not choices:
        return {}
    return (choices[0] or {}).get("message") or {}
