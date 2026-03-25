"""
Load `.env` from the repository root (directory that contains `cyberAI/`).

Also exposes OpenAI-compatible LLM settings (DeepSeek, OpenRouter, etc.) so all
`cyberAI/llm` code reads the same env vars from the project root `.env`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    """Parent of `cyberAI/` — the project root when this file lives in `cyberAI/llm/`."""
    return Path(__file__).resolve().parent.parent.parent


def load_project_dotenv() -> None:
    """Load root `.env` first with override=True; then optional cwd `.env` without overriding."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    env_path = repo_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=True)
    load_dotenv(override=False)


def normalize_openai_api_base(url: str) -> str:
    """
    Normalize base URL for `{base}/v1/chat/completions`.

    Strips trailing slashes and removes a trailing `/v1` so we do not produce
    `/v1/v1/chat/completions` when `.env` already includes `/v1`.
    """
    u = url.strip().rstrip("/")
    if u.endswith("/v1"):
        u = u[: -len("/v1")].rstrip("/")
    return u


@dataclass(frozen=True)
class OpenAICompatibleLLMConfig:
    """OpenAI-style chat completions endpoint (DeepSeek, OpenRouter, etc.)."""

    api_key: str
    base_url: str
    model: str
    extra_headers: dict[str, str]


DEFAULT_DEEPSEEK_BASE = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-reasoner"


def get_openai_compatible_llm_config() -> OpenAICompatibleLLMConfig:
    """
    Read LLM settings after loading project root `.env`.

    API key: `DEEPSEEK_API_KEY`, or `OPENROUTER_API_KEY` if the former is unset.
    Base URL: `DEEPSEEK_BASE_URL` (default official DeepSeek API).
    Model: `DEEPSEEK_MODEL` (non-empty; otherwise default reasoning model).

    Optional OpenRouter headers (see https://openrouter.ai/docs):
    - `OPENROUTER_HTTP_REFERER` → `HTTP-Referer`
    - `OPENROUTER_X_TITLE` → `X-Title`
    """
    load_project_dotenv()

    key = (
        os.environ.get("DEEPSEEK_API_KEY", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
    )
    raw_base = os.environ.get("DEEPSEEK_BASE_URL", "").strip() or DEFAULT_DEEPSEEK_BASE
    base_url = normalize_openai_api_base(raw_base)

    model = os.environ.get("DEEPSEEK_MODEL", "").strip() or DEFAULT_DEEPSEEK_MODEL

    extra: dict[str, str] = {}
    referer = os.environ.get("OPENROUTER_HTTP_REFERER", "").strip()
    if referer:
        extra["HTTP-Referer"] = referer
    title = os.environ.get("OPENROUTER_X_TITLE", "").strip()
    if title:
        extra["X-Title"] = title

    return OpenAICompatibleLLMConfig(
        api_key=key,
        base_url=base_url,
        model=model,
        extra_headers=extra,
    )
