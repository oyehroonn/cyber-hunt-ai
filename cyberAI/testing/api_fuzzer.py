"""
ASRTS §4.2: RESTler-style stateful API fuzzing.
From OpenAPI/endpoint list, build simple dependency sequences (create → get); fuzz with safe/boundary values.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import Finding, HttpMethod, RequestRecord, Severity, TestCategory
from cyberAI.utils.helpers import load_json

FUZZ_STRINGS = ["", "test", "1", "0", "-1", "999999", "a" * 100, "' OR '1'='1", "../", "%00"]
FUZZ_INT_LIKE = [1, 0, -1, 999999999]
MAX_SEQUENCES = 20
MAX_FUZZ_PER_ENDPOINT = 5


async def run_api_fuzzer(
    base_url: str,
    run_id: Optional[str] = None,
    spec_path: Optional[Path] = None,
    client: Optional[Any] = None,
) -> list[Finding]:
    """
    Load endpoints from spec or recon; generate create→read sequences; fuzz params; report 5xx/crashes.
    """
    config = get_config()
    run_id = run_id or getattr(config, "run_id", "") or ""
    findings: list[Finding] = []

    if client is None:
        try:
            from cyberAI.utils.http_client import AsyncHTTPClient
            client = AsyncHTTPClient()
        except ImportError:
            logger.warning("API fuzzer: AsyncHTTPClient not available")
            return findings

    path = spec_path or config.get_output_path("recon", "intelligence", "api_spec_endpoints.json")
    if not path.exists():
        path = config.get_output_path("recon", "intelligence", "endpoints.json")
    if not path.exists():
        logger.debug("API fuzzer: no endpoint list found")
        return findings

    data = load_json(path)
    endpoints = (data or {}).get("endpoints") or []
    create_like = [e for e in endpoints if (e.get("method") in ("POST", "post") and ("create" in (e.get("path_pattern") or "").lower() or "post" in (e.get("url") or "").lower()))]
    read_like = [e for e in endpoints if e.get("method") in ("GET", "get") and ("{id}" in (e.get("path_pattern") or e.get("url") or "") or "/" in (e.get("url") or ""))]

    sequences_run = 0
    for _ in range(min(MAX_SEQUENCES, max(len(create_like), 1) * max(len(read_like), 1))):
        if sequences_run >= MAX_SEQUENCES:
            break
        for post_ep in (create_like or [{}])[:3]:
            for get_ep in (read_like or [{}])[:3]:
                if sequences_run >= MAX_SEQUENCES:
                    break
                url_post = (post_ep.get("url") or "").replace("{id}", "1")
                url_get = (get_ep.get("url") or "").replace("{id}", "1")
                if not url_post and not url_get:
                    continue
                try:
                    if url_post:
                        resp, rec = await client.post(url_post, json={}, record=True)
                        if resp and getattr(resp, "status_code", 0) >= 500 and rec:
                            findings.append(
                                Finding(
                                    title="API fuzzer: 5xx on create",
                                    severity=Severity.MEDIUM,
                                    category=TestCategory.INPUT,
                                    asset=url_post,
                                    request_proof=rec,
                                    evidence_warc_refs=[rec.warc_ref] if getattr(rec, "warc_ref", None) else [],
                                )
                            )
                    if url_get:
                        resp, rec = await client.get(url_get, record=True)
                        if resp and getattr(resp, "status_code", 0) >= 500 and rec:
                            findings.append(
                                Finding(
                                    title="API fuzzer: 5xx on read",
                                    severity=Severity.MEDIUM,
                                    category=TestCategory.INPUT,
                                    asset=url_get,
                                    request_proof=rec,
                                    evidence_warc_refs=[rec.warc_ref] if getattr(rec, "warc_ref", None) else [],
                                )
                            )
                    sequences_run += 1
                except Exception as e:
                    logger.debug(f"API fuzzer sequence: {e}")

    # Fuzz a few GET endpoints with boundary values in path/query
    fuzz_count = 0
    for ep in read_like[:10]:
        if fuzz_count >= MAX_FUZZ_PER_ENDPOINT * 5:
            break
        url_tpl = ep.get("url") or ep.get("path_pattern") or ""
        for val in FUZZ_STRINGS[:MAX_FUZZ_PER_ENDPOINT]:
            url = url_tpl.replace("{id}", str(val)).replace("{uuid}", str(val))
            if url == url_tpl:
                continue
            try:
                resp, rec = await client.get(url, record=True)
                if resp and getattr(resp, "status_code", 0) >= 500 and rec:
                    findings.append(
                        Finding(
                            title="API fuzzer: 5xx on fuzz input",
                            severity=Severity.MEDIUM,
                            category=TestCategory.INPUT,
                            asset=url,
                            request_proof=rec,
                            raw_evidence={"fuzz_value": val},
                            evidence_warc_refs=[rec.warc_ref] if getattr(rec, "warc_ref", None) else [],
                        )
                    )
                fuzz_count += 1
            except Exception as e:
                logger.debug(f"API fuzzer fuzz: {e}")

    out_path = config.get_output_path("testing", "findings", "api_fuzzer_findings.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json
    atomic_write_json(out_path, add_meta_to_output({"findings": [f.model_dump() for f in findings]}, target_url=base_url, phase="test", run_id=run_id))
    logger.info(f"API fuzzer: {len(findings)} findings")
    return findings
