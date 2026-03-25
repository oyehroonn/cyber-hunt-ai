"""
LLM CLIENT - RAG Pipeline Integration

Connects the CyberAI testing pipeline to the RAG knowledge base trained on
242 vulnerability reports (CVEs, CWEs, HackerOne, PortSwigger, etc.).

All function signatures are preserved from the stub so the rest of the
codebase works without changes. Just set LLM_ENABLED=true in .env.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Path bootstrap: make 'llm' resolve to cyberAI/llm/
# ─────────────────────────────────────────────────────────────
_cyberai_dir = str(Path(__file__).parent.parent)
if _cyberai_dir not in sys.path:
    sys.path.insert(0, _cyberai_dir)

# Load project root .env before RAGEngine reads os.environ (same keys as cyberAI.main)
try:
    from llm.project_env import load_project_dotenv

    load_project_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────
# Lazy singleton RAG engine
# ─────────────────────────────────────────────────────────────
_engine: Optional[Any] = None
_engine_failed: bool = False
_last_engine_error: Optional[str] = None


def _get_engine() -> Optional[Any]:
    """Lazy-initialize the RAG engine. Returns None if unavailable or no model."""
    global _engine, _engine_failed, _last_engine_error
    if _engine_failed:
        return None
    if _engine is not None:
        return _engine
    try:
        from llm.project_env import load_project_dotenv

        load_project_dotenv()

        from llm.rag_engine import create_rag_engine

        data_dir = Path(__file__).resolve().parent / "data"
        candidate = create_rag_engine(data_dir=data_dir)
        if not (candidate.model_name and str(candidate.model_name).strip()):
            _last_engine_error = "No LLM model name (set DEEPSEEK_MODEL / Ollama or API keys in project root .env)."
            logger.warning("RAG: %s", _last_engine_error)
            _engine_failed = True
            return None
        _engine = candidate
        _last_engine_error = None
        return _engine
    except Exception as e:
        _last_engine_error = f"{type(e).__name__}: {e}"
        logger.exception("RAG engine initialization failed: %s", e)
        _engine_failed = True
        return None


def get_last_engine_error() -> Optional[str]:
    """Last init error message, if `_get_engine()` returned None."""
    return _last_engine_error


# ─────────────────────────────────────────────────────────────
# Public API — same signatures as the original stub
# ─────────────────────────────────────────────────────────────

def call_llm(prompt: str, context: list[str] = []) -> str:
    """
    Main LLM interface - send a prompt with optional context chunks.

    Args:
        prompt: The question or instruction for the LLM
        context: List of context strings (recon data, findings, code snippets)

    Returns:
        LLM response string, or placeholder if RAG unavailable
    """
    engine = _get_engine()
    if engine is None:
        return "[LLM_NOT_CONFIGURED] RAG engine unavailable. Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY in project root .env, or use Ollama."

    try:
        context_str = "\n\n---\n\n".join(context) if context else ""
        full_prompt = f"{prompt}\n\nAdditional Context:\n{context_str}" if context_str else prompt
        return engine.generate(
            full_prompt,
            variables={"query": prompt[:300]},
            n_context=5,
        )
    except Exception as e:
        return f"[RAG_ERROR] {e}"


def summarize_finding(finding_dict: dict) -> str:
    """
    Summarize a security finding in plain language.

    Args:
        finding_dict: Finding data as dictionary

    Returns:
        Plain language finding summary with impact and remediation hints
    """
    engine = _get_engine()
    if engine is None:
        title = finding_dict.get("title", "Unknown Finding")
        severity = finding_dict.get("severity", "unknown")
        asset = finding_dict.get("asset", "unknown asset")
        return f"Finding: {title} ({severity}) affecting {asset}"

    try:
        return engine.write_finding_report(finding_dict)
    except Exception as e:
        title = finding_dict.get("title", "Unknown Finding")
        return f"Finding: {title} — summary unavailable ({e})"


def generate_attack_hypothesis(intel_dict: dict) -> str:
    """
    Generate attack hypotheses from reconnaissance data.

    Args:
        intel_dict: Intelligence data as dictionary (master_intel content)

    Returns:
        Attack hypothesis text based on RAG knowledge base
    """
    engine = _get_engine()
    if engine is None:
        return "[LLM_NOT_CONFIGURED] Attack hypothesis generation unavailable."

    try:
        result = engine.analyze_recon(intel_dict)
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        return str(result)
    except Exception as e:
        return f"[RAG_ERROR] {e}"


def suggest_test_cases(object_model: dict, permission_matrix: dict) -> list[str]:
    """
    Suggest additional test cases from the vulnerability knowledge base.

    Args:
        object_model: Application object/entity model
        permission_matrix: Permission matrix data

    Returns:
        List of suggested test case descriptions
    """
    engine = _get_engine()
    if engine is None:
        return []

    try:
        hypotheses = engine.generate_hypotheses(object_model, permission_matrix)
        suggestions: list[str] = []
        for h in hypotheses:
            if isinstance(h, dict):
                desc = (
                    h.get("description")
                    or h.get("attack")
                    or h.get("test_name")
                    or str(h)[:200]
                )
                suggestions.append(str(desc))
            else:
                suggestions.append(str(h)[:200])
        return suggestions
    except Exception:
        return []


def analyze_code_for_vulnerabilities(code: str, language: str = "javascript") -> list[dict]:
    """
    Analyze a code snippet for potential vulnerabilities.

    Args:
        code: Source code to analyze
        language: Programming language of the snippet

    Returns:
        List of potential vulnerability dicts with type, severity, description
    """
    engine = _get_engine()
    if engine is None:
        return []

    try:
        prompt = (
            f"Analyze this {language} code for security vulnerabilities. "
            f"Return ONLY a JSON array, each item with: type, severity, description.\n\n"
            f"```{language}\n{code[:3000]}\n```"
        )
        response = engine.generate(
            prompt,
            variables={"query": f"{language} code vulnerability audit"},
            n_context=3,
        )
        json_match = re.search(r"\[[\s\S]*\]", response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return [{"type": "analysis", "severity": "unknown", "description": response[:500]}]
    except Exception:
        return []


def generate_remediation_advice(finding_dict: dict) -> str:
    """
    Generate specific remediation advice for a finding.

    Args:
        finding_dict: Finding data as dictionary

    Returns:
        Actionable remediation steps from the knowledge base
    """
    engine = _get_engine()
    if engine is None:
        vuln_type = finding_dict.get("category", "vulnerability")
        return f"See OWASP guidelines for {vuln_type}."

    try:
        vuln_type = finding_dict.get("category", finding_dict.get("type", "vulnerability"))
        title = finding_dict.get("title", "")
        severity = finding_dict.get("severity", "unknown")

        prompt = (
            f"Provide specific, actionable remediation steps for this {severity} security finding.\n\n"
            f"Title: {title}\nVulnerability Type: {vuln_type}\n"
            f"Details: {json.dumps(finding_dict, indent=2)[:800]}\n\n"
            f"Include: root cause fix, code-level guidance, and validation steps."
        )
        return engine.generate(
            prompt,
            variables={"query": f"{vuln_type} remediation fix patch"},
            n_context=4,
        )
    except Exception as e:
        return f"See OWASP guidelines for {finding_dict.get('category', 'this vulnerability')}."


def explain_impact(finding_dict: dict, business_context: str = "") -> str:
    """
    Explain the business impact of a finding for stakeholders.

    Args:
        finding_dict: Finding data as dictionary
        business_context: Optional description of the business/application

    Returns:
        Clear business impact explanation for non-technical stakeholders
    """
    engine = _get_engine()
    if engine is None:
        severity = finding_dict.get("severity", "")
        category = finding_dict.get("category", "vulnerability")
        return f"This {severity} {category} finding may impact confidentiality, integrity, or availability."

    try:
        vuln_type = finding_dict.get("category", "vulnerability")
        severity = finding_dict.get("severity", "unknown")
        asset = finding_dict.get("asset", "the application")

        prompt = (
            f"Explain the real-world business impact of this {severity} {vuln_type} vulnerability "
            f"in clear terms for executives and non-technical stakeholders.\n\n"
            f"Affected Asset: {asset}\n"
            f"Business Context: {business_context or 'Web application'}\n"
            f"Finding Details: {json.dumps(finding_dict, indent=2)[:600]}\n\n"
            f"Cover: data at risk, regulatory implications, and financial impact."
        )
        return engine.generate(
            prompt,
            variables={"query": f"{vuln_type} business impact risk"},
            n_context=3,
        )
    except Exception as e:
        severity = finding_dict.get("severity", "")
        return f"This {severity} finding may expose sensitive data and impact business operations."


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("LLM Client — RAG Integration Test")
    print("-" * 50)

    engine = _get_engine()
    if engine:
        print(f"RAG engine initialized. Model: {engine.model_name}")
    else:
        err = get_last_engine_error()
        print("RAG engine unavailable.")
        if err:
            print(f"Reason: {err}")
        else:
            print("(check project root .env: DEEPSEEK_API_KEY or OPENROUTER_API_KEY, or Ollama)")

    r = call_llm("List 3 common IDOR vulnerability patterns.", ["Context: REST API with integer IDs"])
    print(f"\ncall_llm response (first 200 chars):\n{r[:200]}")

    s = suggest_test_cases({"User": {"fields": ["id", "email"]}}, {"user": {"read": True}})
    print(f"\nsuggest_test_cases ({len(s)} suggestions): {s[:2]}")

    print("-" * 50)
    print("Done.")
