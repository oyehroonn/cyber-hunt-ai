"""
ASRTS §3.2: Deep web form mining.
Discover forms from crawled pages; fingerprint (action, method, fields); submit adaptive queries with caps.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import HttpMethod, RequestRecord
from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json

# Default payloads for form fields (search, filters) - cap total submissions per form
DEFAULT_FORM_PAYLOADS = ["", "test", "1", "admin", "user", "*", "a", "search", "query", "0"]
MAX_SUBMISSIONS_PER_FORM = 10
MAX_FORMS_PER_PAGE = 20


@dataclass
class FormFingerprint:
    """Fingerprint of a form for deduplication."""
    action: str
    method: str
    field_names: tuple[str, ...]


def _parse_forms_from_html(html: str, base_url: str) -> list[FormFingerprint]:
    """Extract form action, method, and field names from HTML."""
    forms = []
    # Find <form ... action="..." method="..."> and collect input/select/textarea name=
    form_pattern = re.compile(
        r'<form[^>]*\baction\s*=\s*["\']([^"\']*)["\'][^>]*\bmethod\s*=\s*["\'](get|post)["\']',
        re.I,
    )
    form_pattern2 = re.compile(
        r'<form[^>]*\bmethod\s*=\s*["\'](get|post)["\'][^>]*\baction\s*=\s*["\']([^"\']*)["\']',
        re.I,
    )
    name_pattern = re.compile(r'<(?:input|select|textarea)[^>]*\bname\s*=\s*["\']([^"\']+)["\']', re.I)

    for m in form_pattern.finditer(html):
        action, method = m.group(1).strip(), m.group(2).upper()
        end = html.find("</form>", m.end())
        block = html[m.start():end] if end != -1 else html[m.start():m.start() + 5000]
        names = tuple(sorted(set(name_pattern.findall(block))))
        action_full = urljoin(base_url, action) if action else base_url
        forms.append(FormFingerprint(action=action_full, method=method, field_names=names))

    for m in form_pattern2.finditer(html):
        method, action = m.group(1).upper(), m.group(2).strip()
        end = html.find("</form>", m.end())
        block = html[m.start():end] if end != -1 else html[m.start():m.start() + 5000]
        names = tuple(sorted(set(name_pattern.findall(block))))
        action_full = urljoin(base_url, action) if action else base_url
        forms.append(FormFingerprint(action=action_full, method=method, field_names=names))

    return forms[:MAX_FORMS_PER_PAGE]


async def run_form_mining(
    routes: list[Any],
    base_url: str,
    run_id: Optional[str] = None,
    network_intel: Optional[Any] = None,
    max_submissions_per_form: int = MAX_SUBMISSIONS_PER_FORM,
) -> list[RequestRecord]:
    """
    Discover forms from route DOMs; submit adaptive queries; return new RequestRecords.
    If network_intel is provided, appends records to it.
    """
    config = get_config()
    run_id = run_id or getattr(config, "run_id", "") or ""
    seen_fingerprints: set[tuple[str, str, tuple[str, ...]]] = set()
    records: list[RequestRecord] = []

    try:
        from cyberAI.utils.http_client import AsyncHTTPClient
    except ImportError:
        logger.warning("Form mining: AsyncHTTPClient not available")
        return records

    client = AsyncHTTPClient()
    payloads = DEFAULT_FORM_PAYLOADS[:max_submissions_per_form]

    for route in routes:
        html = None
        page_url = getattr(route, "url", None) or base_url
        dom_path = getattr(route, "dom_path", None)
        if dom_path and Path(dom_path).is_file():
            try:
                html = Path(dom_path).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.debug(f"Form mining: read DOM {dom_path}: {e}")
        if not html:
            try:
                resp = await client.get(page_url)
                if resp and getattr(resp, "text", None):
                    html = resp.text
            except Exception as e:
                logger.debug(f"Form mining: fetch {page_url}: {e}")
        if not html:
            continue

        forms = _parse_forms_from_html(html, page_url)
        for fp in forms:
            key = (fp.action, fp.method, fp.field_names)
            if key in seen_fingerprints:
                continue
            seen_fingerprints.add(key)

            for payload_index, value in enumerate(payloads):
                if payload_index >= max_submissions_per_form:
                    break
                try:
                    if fp.method == "GET":
                        query = "&".join(f"{n}={value}" for n in fp.field_names) if fp.field_names else ""
                        url = f"{fp.action}&{query}" if "?" in fp.action else f"{fp.action}?{query}"
                        resp, rec = await client.get(url, record=True)
                    else:
                        data = {n: value for n in fp.field_names} if fp.field_names else {}
                        resp, rec = await client.post(fp.action, data=data, record=True)

                    if rec is not None:
                        records.append(rec)
                    elif resp is not None and hasattr(resp, "status_code"):
                        records.append(
                            RequestRecord(
                                method=HttpMethod.GET if fp.method == "GET" else HttpMethod.POST,
                                url=fp.action,
                                response_status=getattr(resp, "status_code", 0),
                                response_content_type=dict(getattr(resp, "headers", {})).get("content-type") if hasattr(resp, "headers") else None,
                                response_body=getattr(resp, "text", None),
                            )
                        )
                except Exception as e:
                    logger.debug(f"Form submit {fp.action}: {e}")

    if network_intel and records:
        network_intel.add_requests(records, role_context=None)

    out_path = config.get_output_path("recon", "intelligence", "form_mining_requests.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        out_path,
        add_meta_to_output(
            {"requests": [r.model_dump() for r in records], "count": len(records)},
            target_url=base_url,
            phase="recon",
            run_id=run_id,
        ),
    )
    logger.info(f"Form mining: {len(records)} requests from forms")
    return records
