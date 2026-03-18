"""
ASRTS §3.4: Sensitive exposure detection.
Lexical pass: regex for PII, credentials, API keys in response bodies.
Relevance gate: only run on responses above security relevance threshold.
Store WARC ref + snippet in finding, not full body.
"""

import re
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Finding, RequestRecord, Severity, TestCategory
from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json, load_json

# Patterns: (name, regex, max_snippet_len)
LEXICAL_PATTERNS = [
    ("api_key", re.compile(r"(?i)(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", re.I), 40),
    ("secret", re.compile(r"(?i)(?:secret|password|passwd)\s*[:=]\s*['\"]?([^\s'\"]{6,})['\"]?", re.I), 30),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}", re.I), 24),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", re.I), 50),
    ("generic_token", re.compile(r"(?i)(?:token|bearer|auth)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{20,})['\"]?", re.I), 40),
    ("private_key_header", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", re.I), 50),
    ("credit_card_like", re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"), 20),
]

RELEVANCE_MIN_SCORE = 0.2  # Only scan responses from URLs with this security relevance


def _relevance_score(url: str) -> float:
    """Security relevance of URL (reuse priority scorer if available)."""
    try:
        from cyberAI.recon.priority_scorer import score_url_security_relevance
        return score_url_security_relevance(url)
    except ImportError:
        u = url.lower()
        if any(x in u for x in ["api", "admin", "user", "auth", "token", "key", "secret"]):
            return 0.6
        return 0.3


def _scan_body(body: str, url: str) -> list[dict]:
    """Run lexical patterns; return list of {type, snippet, start}."""
    if not body or not isinstance(body, str):
        return []
    results = []
    for name, pattern, max_len in LEXICAL_PATTERNS:
        for m in pattern.finditer(body):
            snippet = m.group(0) if m.lastindex is None else (m.group(1) or m.group(0))
            if len(snippet) > max_len:
                snippet = snippet[: max_len - 3] + "..."
            results.append({"type": name, "snippet": snippet, "start": m.start()})
    return results


def run_sensitive_exposure(
    requests: list[RequestRecord],
    run_id: Optional[str] = None,
    relevance_min: float = RELEVANCE_MIN_SCORE,
) -> list[Finding]:
    """
    Scan response bodies for sensitive patterns; emit findings with WARC ref and snippet only.
    Only runs on requests whose URL has relevance >= relevance_min.
    """
    config = get_config()
    run_id = run_id or getattr(config, "run_id", "") or ""
    findings: list[Finding] = []

    for rec in requests:
        if _relevance_score(rec.url) < relevance_min:
            continue
        body = rec.response_body or ""
        ct = (getattr(rec, "response_content_type", None) or "").lower()
        # ASRTS 3.4.2: For image/PDF, run OCR first then lexical on extracted text
        if body and ("image/" in ct or "pdf" in ct):
            try:
                from cyberAI.recon.ocr_extract import extract_text_from_response
                ocr_text = extract_text_from_response(body, ct)
                if ocr_text:
                    body = ocr_text
            except Exception as e:
                logger.debug(f"OCR for sensitive exposure: {e}")
        if not body or not isinstance(body, str):
            continue
        matches = _scan_body(body, rec.url)
        for m in matches:
            finding = Finding(
                title=f"Possible {m['type'].replace('_', ' ')} in response",
                severity=Severity.LOW,
                category=TestCategory.CONFIG,
                asset=rec.url,
                raw_evidence={
                    "snippet": m["snippet"],
                    "pattern_type": m["type"],
                    "url": rec.url,
                },
                evidence_warc_refs=[rec.warc_ref] if getattr(rec, "warc_ref", None) else [],
            )
            findings.append(finding)

    out_path = config.get_output_path("testing", "findings", "sensitive_exposure_findings.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        out_path,
        add_meta_to_output(
            {"findings": [f.model_dump() for f in findings], "count": len(findings)},
            target_url=getattr(config, "target_url", "") or "",
            phase="recon",
            run_id=run_id,
        ),
    )
    logger.info(f"Sensitive exposure: {len(findings)} potential findings")
    return findings


def run_sensitive_exposure_from_intel(
    run_id: Optional[str] = None,
    requests_path: Optional[Path] = None,
) -> list[Finding]:
    """
    Load requests from recon output (all_requests.json) and run sensitive exposure.
    """
    config = get_config()
    path = requests_path or config.get_output_path("recon", "requests", "all_requests.json")
    data = load_json(path)
    requests_list = (data or {}).get("requests") or []
    from cyberAI.models import HttpMethod
    records = []
    for r in requests_list:
        if isinstance(r, dict):
            method = r.get("method", "GET")
            if isinstance(method, str):
                method = getattr(HttpMethod, method.upper(), HttpMethod.GET)
            records.append(
                RequestRecord(
                    method=method,
                    url=r.get("url", ""),
                    response_status=r.get("response_status", 0),
                    response_body=r.get("response_body"),
                    warc_ref=r.get("warc_ref"),
                )
            )
    return run_sensitive_exposure(records, run_id=run_id)
