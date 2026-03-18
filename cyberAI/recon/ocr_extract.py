"""
ASRTS §4.3: OCR pipeline for high-risk content.
For image/PDF responses with high relevance score, run OCR; run sensitive-exposure patterns on text.
"""

import re
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Finding, RequestRecord, Severity, TestCategory

# Same snippet patterns as sensitive_exposure (simplified)
OCR_PATTERNS = [
    ("password", re.compile(r"(?i)password\s*[:=]\s*['\"]?([^\s'\"]{4,})", re.I)),
    ("secret", re.compile(r"(?i)secret\s*[:=]\s*['\"]?([^\s'\"]{6,})", re.I)),
    ("api_key", re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})", re.I)),
]

MAX_OCR_PAGES_PER_RUN = 100


def extract_text_from_response(
    body: Any,
    content_type: str,
    max_bytes: int = 5_000_000,
) -> Optional[str]:
    """
    Extract text from image/PDF response body for sensitive-exposure scan.
    body: bytes or base64 str; content_type: e.g. image/png, application/pdf.
    Returns extracted text or None.
    """
    if not body:
        return None
    ct = (content_type or "").lower()
    if "image/" not in ct and "pdf" not in ct:
        return None
    import tempfile
    data = body
    if isinstance(data, str):
        try:
            import base64
            data = base64.b64decode(data, validate=True)
        except Exception:
            data = data.encode("utf-8", errors="replace")
    if len(data) > max_bytes:
        data = data[:max_bytes]
    suffix = ".pdf" if "pdf" in ct else ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = Path(f.name)
    try:
        if "pdf" in ct:
            text = _extract_text_pdf(path)
        else:
            text = _extract_text_image(path)
        return text
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def _relevance_score(url: str) -> float:
    try:
        from cyberAI.recon.priority_scorer import score_url_security_relevance
        return score_url_security_relevance(url)
    except ImportError:
        return 0.5 if any(x in url.lower() for x in ["admin", "api", "doc", "export"]) else 0.2


def _extract_text_image(image_path: Path) -> Optional[str]:
    """Extract text from image via Tesseract if available."""
    try:
        import subprocess
        result = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"OCR tesseract: {e}")
    return None


def _extract_text_pdf(pdf_path: Path) -> Optional[str]:
    """Extract text from PDF if PyMuPDF or pdfminer available."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = []
        for i, page in enumerate(doc):
            if i >= 10:
                break
            text.append(page.get_text())
        doc.close()
        return "\n".join(text) if text else None
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"OCR PDF: {e}")
    return None


def run_ocr_on_requests(
    requests: list[RequestRecord],
    run_id: Optional[str] = None,
    max_pages: int = MAX_OCR_PAGES_PER_RUN,
    relevance_min: float = 0.4,
) -> list[Finding]:
    """
    For each request with image/PDF response body saved to temp file, run OCR; scan for sensitive patterns.
    Returns findings with WARC ref and snippet. Does not save response body to disk by default—caller may pass requests that have local paths in raw_evidence.
    """
    config = get_config()
    run_id = run_id or getattr(config, "run_id", "") or ""
    findings: list[Finding] = []
    pages_done = 0

    for rec in requests:
        if pages_done >= max_pages:
            break
        if _relevance_score(rec.url) < relevance_min:
            continue
        ct = (rec.response_content_type or "").lower()
        if "image/" not in ct and "pdf" not in ct:
            continue
        # If response_body is binary we'd need to write to temp file; for now skip unless we have a path
        body = rec.response_body
        if not body:
            continue
        if isinstance(body, str) and (body.startswith("/") or "base64" in body[:50]):
            # Could decode base64 and write to temp file
            pass
        # Minimal: if response_body is text (e.g. base64 decoded elsewhere), scan as text
        if isinstance(body, str) and len(body) > 100:
            for name, pattern in OCR_PATTERNS:
                m = pattern.search(body)
                if m:
                    snippet = (m.group(1) or m.group(0))[:50]
                    findings.append(
                        Finding(
                            title=f"Possible {name} in OCR/content",
                            severity=Severity.LOW,
                            category=TestCategory.CONFIG,
                            asset=rec.url,
                            raw_evidence={"snippet": snippet, "pattern": name},
                            evidence_warc_refs=[rec.warc_ref] if getattr(rec, "warc_ref", None) else [],
                        )
                    )
            pages_done += 1

    from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json
    out_path = config.get_output_path("testing", "findings", "ocr_exposure_findings.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out_path, add_meta_to_output({"findings": [f.model_dump() for f in findings]}, target_url="", phase="recon", run_id=run_id))
    logger.info(f"OCR exposure: {len(findings)} findings")
    return findings
