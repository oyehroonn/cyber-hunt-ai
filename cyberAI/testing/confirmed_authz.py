"""
Confirmatory authorization tests (target-agnostic):
- Differential session replay (two roles) with explicit confirmation metadata
- Unauthenticated vs authenticated access to sensitive-looking JSON endpoints
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Optional
from urllib.parse import urljoin

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    Finding,
    ImpactType,
    ReproductionStep,
    RequestRecord,
    Severity,
    TestCategory,
)
from cyberAI.testing.authorization_testing import AuthorizationTester
from cyberAI.utils.helpers import load_json
from cyberAI.utils.http_client import AsyncHTTPClient


_SENSITIVE_HINTS = (
    "profile",
    "account",
    "user",
    "order",
    "cart",
    "wallet",
    "payment",
    "invoice",
    "session",
    "token",
    "credential",
    "admin",
    "me",
    "/users/",
    "/rest/",
)

_STATIC_EXT = (".js", ".css", ".png", ".jpg", ".ico", ".woff", ".svg", ".map")


def _is_skippable_url(url: str) -> bool:
    u = url.lower()
    if any(u.endswith(ext) for ext in _STATIC_EXT):
        return True
    if "/static/" in u or "/assets/" in u:
        return True
    return False


def _normalize_json_body(text: str) -> str:
    try:
        return json.dumps(json.loads(text), sort_keys=True)
    except Exception:
        return text


async def _unauth_vs_auth_findings(run_id: str) -> list[Finding]:
    config = get_config()
    base = (config.target_url or "").rstrip("/")
    if not base or not config.role_accounts:
        return []

    ep_data = load_json(config.get_output_path("recon", "intelligence", "endpoint_inventory.json")) or {}
    endpoints = ep_data.get("endpoints") if isinstance(ep_data, dict) else []
    if not endpoints:
        mi = load_json(config.get_output_path("recon", "intelligence", "master_intel.json")) or {}
        endpoints = mi.get("endpoints") or []

    from cyberAI.identity.session_store import SessionStore

    store = SessionStore(config.get_output_path("sessions", "sessions.json"))
    acc = config.role_accounts[0]
    sess = store.get(run_id, acc.role)
    if not sess or not sess.get("cookies"):
        return []

    findings: list[Finding] = []
    client = AsyncHTTPClient()
    try:
        for ep in endpoints[:60]:
            url = ep.get("url") if isinstance(ep, dict) else None
            if not url and isinstance(ep, dict):
                p = ep.get("path") or ep.get("path_pattern") or ""
                if p and not p.startswith("http"):
                    url = urljoin(base + "/", p.lstrip("/"))
            if not url or not str(url).startswith("http"):
                continue
            if _is_skippable_url(url):
                continue
            if not any(h in url.lower() for h in _SENSITIVE_HINTS):
                continue

            resp_u, rec_u = await client.get(url, follow_redirects=False, record=True)
            client.clear_cookies()
            client.set_cookies(sess["cookies"])
            resp_a, rec_a = await client.get(url, follow_redirects=False, record=True)
            client.clear_cookies()

            ct_u = (resp_u.headers.get("content-type") or "").lower()
            ct_a = (resp_a.headers.get("content-type") or "").lower()
            if resp_u.status_code != 200 or resp_a.status_code != 200:
                await asyncio.sleep(config.request_delay_ms / 1000)
                continue
            if "application/json" not in ct_u or "application/json" not in ct_a:
                await asyncio.sleep(config.request_delay_ms / 1000)
                continue

            bu = resp_u.text or ""
            ba = resp_a.text or ""
            if len(bu) < 80 or len(ba) < 80:
                await asyncio.sleep(config.request_delay_ms / 1000)
                continue

            hu = hashlib.sha256(_normalize_json_body(bu).encode()).hexdigest()[:16]
            ha = hashlib.sha256(_normalize_json_body(ba).encode()).hexdigest()[:16]
            # Same substantive JSON without auth as with auth — likely missing authentication on sensitive API
            if hu == ha:
                findings.append(
                    Finding(
                        title=f"[Confirmed] Unauthenticated access matches authenticated response: {url[:80]}",
                        severity=Severity.HIGH,
                        category=TestCategory.CONFIRMED_AUTHZ,
                        asset=url,
                        reproduction_steps=[
                            ReproductionStep(
                                step_number=1,
                                action=f"GET {url} (no session)",
                                actual_result=f"200 {len(bu)} bytes",
                            ),
                            ReproductionStep(
                                step_number=2,
                                action=f"GET {url} (session {acc.role})",
                                actual_result=f"200 {len(ba)} bytes (same hash)",
                            ),
                        ],
                        reliability_score=82.0,
                        root_cause="Sensitive endpoint returns same JSON with and without session",
                        request_proof=rec_u,
                        response_proof=rec_u.response_body_preview if rec_u else None,
                        impact_types=[ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY],
                        cwe_id="CWE-306",
                        raw_evidence={
                            "confirmation_method": "unauthenticated_vs_authenticated_same_body",
                            "body_hash_unauth": hu,
                            "body_hash_auth": ha,
                            "role": acc.role,
                        },
                    )
                )
            await asyncio.sleep(config.request_delay_ms / 1000)
    finally:
        await client.close()

    return findings


async def run_confirmed_authz_tests(run_id: Optional[str] = None) -> list[Finding]:
    """
    Run confirmatory BOLA/differential + unauth vs auth checks.
    """
    config = get_config()
    rid = run_id or config.run_id or "default"
    findings: list[Finding] = []

    # 1) Differential (reuse AuthorizationTester)
    if len(config.role_accounts) >= 2:
        roles = [a.role for a in config.role_accounts[:2]]
        tester = AuthorizationTester(run_id=rid)
        try:
            diff = await tester.test_differential_auth(
                role_high=roles[0],
                role_low=roles[1],
                engagement_id=rid,
            )
            for f in diff:
                f.raw_evidence = dict(f.raw_evidence or {})
                f.raw_evidence["confirmation_method"] = "differential_two_session"
                f.reliability_score = max(f.reliability_score, 72.0)
                f.category = TestCategory.CONFIRMED_AUTHZ
                if not f.title.startswith("[Confirmed]"):
                    f.title = "[Confirmed] " + f.title
                findings.append(f)
        except Exception as e:
            logger.debug(f"confirmed_authz differential: {e}")

    # 2) Unauth vs auth same body
    try:
        findings.extend(await _unauth_vs_auth_findings(rid))
    except Exception as e:
        logger.debug(f"confirmed_authz unauth_vs_auth: {e}")

    logger.info(f"confirmed_authz: {len(findings)} findings")
    return findings
