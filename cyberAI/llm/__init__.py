"""
LLM integration module for the CyberAI platform (RAG, llm_client).

Exports are loaded lazily so `import llm.project_env` or `from llm.rag_engine import ...`
does not pull in `llm_client` or create circular imports when running `llm_client.py` as __main__.
"""

from __future__ import annotations

__all__ = [
    "call_llm",
    "summarize_finding",
    "generate_attack_hypothesis",
    "suggest_test_cases",
    "analyze_code_for_vulnerabilities",
    "generate_remediation_advice",
    "explain_impact",
]


def __getattr__(name: str):
    if name in __all__:
        from . import llm_client

        return getattr(llm_client, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
