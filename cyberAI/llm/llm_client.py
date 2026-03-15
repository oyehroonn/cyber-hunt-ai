"""
LLM CLIENT STUB

This file will be replaced with the full RAG pipeline integration.
Do NOT remove the function signatures — the rest of the codebase calls these.

The entire system works end-to-end without the LLM; the LLM only enriches
analysis and writes reports. When the RAG client is ready, drop it in here.

Integration Points:
- call_llm(): Main function for prompting the LLM with context
- summarize_finding(): Summarize a security finding in plain language
- generate_attack_hypothesis(): Generate attack hypotheses from recon data
- suggest_test_cases(): Suggest additional test cases from intelligence

To integrate your RAG pipeline:
1. Replace the stub implementations below with your RAG client calls
2. Ensure the function signatures remain unchanged
3. Update config.py LLM_ENABLED to true
4. Test with a simple call to verify integration

Example integration:
```python
from your_rag_client import RAGClient

_rag_client = None

def _get_client():
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient(...)
    return _rag_client

def call_llm(prompt: str, context: list[str] = []) -> str:
    client = _get_client()
    return client.query(prompt, context=context)
```
"""

from typing import Any


def call_llm(prompt: str, context: list[str] = []) -> str:
    """
    Main LLM interface - send a prompt with optional context.
    
    Args:
        prompt: The prompt/question to send to the LLM
        context: List of context strings (e.g., code snippets, findings)
        
    Returns:
        LLM response string
        
    Example:
        response = call_llm(
            "Analyze this endpoint for IDOR vulnerabilities",
            context=[endpoint_json, request_log]
        )
    """
    return "[LLM_NOT_CONFIGURED] Placeholder response. Install RAG client to enable."


def summarize_finding(finding_dict: dict) -> str:
    """
    Summarize a security finding in plain language.
    
    Args:
        finding_dict: Finding data as dictionary
        
    Returns:
        Plain language summary of the finding
        
    Example:
        summary = summarize_finding(finding.model_dump())
    """
    title = finding_dict.get('title', 'Unknown Finding')
    severity = finding_dict.get('severity', 'unknown')
    asset = finding_dict.get('asset', 'unknown asset')
    
    return f"[LLM_NOT_CONFIGURED] Finding: {title} ({severity}) affecting {asset}"


def generate_attack_hypothesis(intel_dict: dict) -> str:
    """
    Generate attack hypothesis from reconnaissance data.
    
    Args:
        intel_dict: Intelligence data as dictionary
        
    Returns:
        Attack hypothesis text
        
    Example:
        hypothesis = generate_attack_hypothesis(master_intel.model_dump())
    """
    return "[LLM_NOT_CONFIGURED] Attack hypothesis generation unavailable. Install RAG client to enable."


def suggest_test_cases(object_model: dict, permission_matrix: dict) -> list[str]:
    """
    Suggest additional test cases based on object model and permissions.
    
    Args:
        object_model: Object model data as dictionary
        permission_matrix: Permission matrix data as dictionary
        
    Returns:
        List of suggested test case descriptions
        
    Example:
        suggestions = suggest_test_cases(
            object.model_dump(),
            permissions.model_dump()
        )
    """
    return []


def analyze_code_for_vulnerabilities(code: str, language: str = "javascript") -> list[dict]:
    """
    Analyze code snippet for potential vulnerabilities.
    
    Args:
        code: Code snippet to analyze
        language: Programming language of the code
        
    Returns:
        List of potential vulnerability dictionaries
    """
    return []


def generate_remediation_advice(finding_dict: dict) -> str:
    """
    Generate remediation advice for a finding.
    
    Args:
        finding_dict: Finding data as dictionary
        
    Returns:
        Remediation advice text
    """
    return "[LLM_NOT_CONFIGURED] Remediation advice unavailable. Install RAG client to enable."


def explain_impact(finding_dict: dict, business_context: str = "") -> str:
    """
    Explain the business impact of a finding.
    
    Args:
        finding_dict: Finding data as dictionary
        business_context: Optional business context description
        
    Returns:
        Business impact explanation
    """
    return "[LLM_NOT_CONFIGURED] Impact explanation unavailable. Install RAG client to enable."


if __name__ == "__main__":
    print("LLM Client Stub - Testing")
    print("-" * 40)
    
    response = call_llm("Test prompt", ["context1", "context2"])
    print(f"call_llm response: {response}")
    
    summary = summarize_finding({"title": "Test Finding", "severity": "high", "asset": "/api/test"})
    print(f"summarize_finding response: {summary}")
    
    hypothesis = generate_attack_hypothesis({"endpoints": [], "objects": []})
    print(f"generate_attack_hypothesis response: {hypothesis}")
    
    suggestions = suggest_test_cases({}, {})
    print(f"suggest_test_cases response: {suggestions}")
    
    print("-" * 40)
    print("All stubs working correctly. Replace with RAG client when ready.")
