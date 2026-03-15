"""
LLM integration module for the CyberAI platform.
Currently contains stubs - replace with RAG client implementation.
"""

from cyberAI.llm.llm_client import (
    call_llm,
    summarize_finding,
    generate_attack_hypothesis,
    suggest_test_cases,
    analyze_code_for_vulnerabilities,
    generate_remediation_advice,
    explain_impact,
)

__all__ = [
    "call_llm",
    "summarize_finding",
    "generate_attack_hypothesis",
    "suggest_test_cases",
    "analyze_code_for_vulnerabilities",
    "generate_remediation_advice",
    "explain_impact",
]
