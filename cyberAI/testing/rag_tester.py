"""
RAG-Powered Security Tester

Uses the vulnerability knowledge base (trained on 242 reports: CVEs, CWEs,
HackerOne, PortSwigger, ExploitDB, PayloadsAllTheThings, etc.) to generate
and execute targeted security tests against the target application.

Integrated into the testing pipeline as the 'rag' category. The RAG engine:
  1. Receives recon data (master_intel.json) as context
  2. Retrieves similar vulnerability patterns from ChromaDB
  3. Generates specific HTTP test requests tailored to the target
  4. The tester executes those requests and analyzes responses
  5. Confirmed signals become findings in the standard pipeline

Usage:
    Automatically runs when categories includes 'rag':
        python -m cyberAI.main test --categories rag
    Or as part of full run:
        python -m cyberAI.main full --target https://example.com
"""

import asyncio
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import httpx
from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import (
    Finding,
    FindingStatus,
    HttpMethod,
    ImpactType,
    RequestRecord,
    ReproductionStep,
    Severity,
    TestCategory,
    TestPlan,
)
from cyberAI.utils.helpers import atomic_write_json, load_json

# Bootstrap: make 'llm' resolve to cyberAI/llm/
_cyberai_dir = str(Path(__file__).parent.parent)
if _cyberai_dir not in sys.path:
    sys.path.insert(0, _cyberai_dir)


# ─────────────────────────────────────────────────────────────
# Vulnerability class definitions
# ─────────────────────────────────────────────────────────────

# Map vuln class → OWASP severity + impact types
VULN_PROFILES: dict[str, dict] = {
    "IDOR": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY],
        "cwe": "CWE-284",
    },
    "SQL Injection": {
        "severity_high": Severity.CRITICAL,
        "severity_low": Severity.HIGH,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY, ImpactType.AVAILABILITY],
        "cwe": "CWE-89",
    },
    "XSS": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY],
        "cwe": "CWE-79",
    },
    "Authentication Bypass": {
        "severity_high": Severity.CRITICAL,
        "severity_low": Severity.HIGH,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY],
        "cwe": "CWE-287",
    },
    "Business Logic": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.INTEGRITY, ImpactType.FINANCIAL],
        "cwe": "CWE-840",
    },
    "SSRF": {
        "severity_high": Severity.CRITICAL,
        "severity_low": Severity.HIGH,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.AVAILABILITY],
        "cwe": "CWE-918",
    },
    "Race Condition": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.INTEGRITY, ImpactType.FINANCIAL],
        "cwe": "CWE-362",
    },
    "File Upload": {
        "severity_high": Severity.CRITICAL,
        "severity_low": Severity.HIGH,
        "impacts": [ImpactType.INTEGRITY, ImpactType.AVAILABILITY],
        "cwe": "CWE-434",
    },
    "Mass Assignment": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.INTEGRITY],
        "cwe": "CWE-915",
    },
    "Authorization Bypass": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY],
        "cwe": "CWE-285",
    },
    "Session Fixation": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.CONFIDENTIALITY],
        "cwe": "CWE-384",
    },
    "CSRF": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.INTEGRITY],
        "cwe": "CWE-352",
    },
    "Command Injection": {
        "severity_high": Severity.CRITICAL,
        "severity_low": Severity.HIGH,
        "impacts": [ImpactType.CONFIDENTIALITY, ImpactType.INTEGRITY, ImpactType.AVAILABILITY],
        "cwe": "CWE-78",
    },
    "Path Traversal": {
        "severity_high": Severity.HIGH,
        "severity_low": Severity.MEDIUM,
        "impacts": [ImpactType.CONFIDENTIALITY],
        "cwe": "CWE-22",
    },
    "Insecure Deserialization": {
        "severity_high": Severity.CRITICAL,
        "severity_low": Severity.HIGH,
        "impacts": [ImpactType.INTEGRITY, ImpactType.AVAILABILITY],
        "cwe": "CWE-502",
    },
}

# Response body patterns that signal vulnerability
VULN_INDICATORS: dict[str, list[str]] = {
    "sql injection": [
        "mysql_fetch", "sql syntax", "syntax error", "pg_query", "sqlite3",
        "ora-", "microsoft jet", "unclosed quotation", "you have an error in your sql",
        "supplied argument is not a valid mysql", "warning: mysql", "division by zero",
        "invalid query", "pg_exec", "supplied argument is not a valid",
    ],
    "xss": [
        "<script>alert", "onerror=alert", "onload=alert", "javascript:alert",
        "document.cookie", "<img src=x onerror", "eval(", "<svg onload",
    ],
    "ssrf": [
        "169.254.169.254", "ec2.internal", "metadata.google.internal",
        "instance-data", "ami-id", "iam/security-credentials",
        "localhost", "127.0.0.1", "::1", "internal.corp",
    ],
    "command injection": [
        "uid=0(root)", "bin/bash", "bin/sh", "/etc/passwd", "root:x:0:0",
        "command not found", "permission denied", "no such file",
        "syntax error near unexpected token",
    ],
    "path traversal": [
        "root:x:0:0", "/etc/passwd", "windows\\system32", "[boot loader]",
        "etc/shadow", "[extensions]", "daemon:x:",
    ],
    "insecure deserialization": [
        "unserialize()", "java.io.serializable", "system.runtime.serialization",
        "objectinputstream", "pickle.loads",
    ],
}


class RAGTester:
    """
    Security tester powered by the RAG knowledge base.

    Generates targeted HTTP attack vectors from the vulnerability knowledge
    base (trained on 242 reports) and executes them against the live target.
    Results feed directly into the standard finding/verification pipeline.
    """

    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self._engine: Optional[Any] = None
        self._engine_failed: bool = False
        self._intel: dict = {}
        self._findings: list[Finding] = []

    # ─────────────────────────────────────────────────────────
    # Engine initialization
    # ─────────────────────────────────────────────────────────

    def _get_engine(self) -> Optional[Any]:
        if self._engine_failed:
            return None
        if self._engine is not None:
            return self._engine
        try:
            from llm.rag_engine import create_rag_engine
            data_dir = Path(__file__).parent.parent / "llm" / "data"
            candidate = create_rag_engine(data_dir=data_dir)
            if not candidate.model_name:
                logger.warning(
                    "RAG Tester: no LLM model configured. "
                    "Set DEEPSEEK_API_KEY in .env or run 'ollama serve' with a model."
                )
                self._engine_failed = True
                return None
            self._engine = candidate
            logger.info(f"RAG Tester: engine initialized, model={self._engine.model_name}")
            return self._engine
        except Exception as e:
            logger.warning(f"RAG Tester: could not initialize engine: {e}")
            self._engine_failed = True
            return None

    # ─────────────────────────────────────────────────────────
    # Intelligence loading
    # ─────────────────────────────────────────────────────────

    def _load_intel(self) -> dict:
        if not self._intel:
            intel_path = self.config.get_output_path(
                "recon", "intelligence", "master_intel.json"
            )
            self._intel = load_json(intel_path) or {}
        return self._intel

    def _load_existing_findings(self) -> list[dict]:
        path = self.config.get_output_path("testing", "findings", "all_findings.json")
        return (load_json(path) or {}).get("findings", [])

    def _build_recon_summary(self, intel: dict) -> str:
        """Compact recon summary for the RAG prompt (< 800 chars)."""
        lines: list[str] = []
        target = intel.get("_meta", {}).get("target_url", self.config.target_url or "")
        if target:
            lines.append(f"Target: {target}")

        if endpoints := intel.get("endpoints", []):
            sample = [e.get("url", "") for e in endpoints[:8] if e.get("url")]
            lines.append(f"Endpoints ({len(endpoints)}): {', '.join(sample)}")

        if objects := intel.get("objects", []):
            names = [o.get("name", "") for o in objects[:8] if o.get("name")]
            lines.append(f"Objects: {', '.join(names)}")

        if routes := intel.get("routes", []):
            urls = [r.get("url", "") for r in routes[:6] if r.get("url")]
            lines.append(f"Routes ({len(routes)}): {', '.join(urls)}")

        if schemas := intel.get("input_schemas", []):
            for s in schemas[:2]:
                ep = s.get("endpoint_url", "")
                fields = str(s.get("fields", [])[:5])
                lines.append(f"Schema [{ep}]: {fields}")

        if workflows := intel.get("workflows", []):
            names = [w.get("name", "") for w in workflows[:5] if w.get("name")]
            lines.append(f"Workflows: {', '.join(names)}")

        return "\n".join(lines) or "Web application (no detailed recon available)"

    def _build_findings_summary(self, findings: list[dict]) -> str:
        if not findings:
            return "No prior findings"
        lines = [
            f"- {f.get('title','?')} [{f.get('severity','?')}] @ {f.get('asset','?')}"
            for f in findings[:8]
        ]
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────
    # HTTP execution
    # ─────────────────────────────────────────────────────────

    async def _execute_request(
        self,
        method: str,
        url: str,
        headers: dict,
        body: Optional[dict],
        timeout: int = 20,
    ) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                verify=False,
                follow_redirects=True,
            ) as client:
                resp = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=body,
                )
                return {
                    "success": True,
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "body": resp.text[:3000],
                    "url": str(resp.url),
                }
        except httpx.InvalidURL:
            return {"success": False, "error": f"Invalid URL: {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────
    # Response assessment
    # ─────────────────────────────────────────────────────────

    def _assess_response(
        self,
        vuln_class: str,
        request_url: str,
        response: dict,
    ) -> Optional[dict]:
        """Return assessment dict if response shows vulnerability signals."""
        if not response.get("success"):
            return None

        status = response.get("status_code", 0)
        body_lower = response.get("body", "").lower()
        vuln_lower = vuln_class.lower()

        # Check body patterns
        for pattern in VULN_INDICATORS.get(vuln_lower, []):
            if pattern in body_lower:
                return {
                    "indicator": pattern,
                    "status_code": status,
                    "confidence": 0.75,
                    "signal_type": "body_pattern",
                }

        # IDOR / auth bypass: 200 where 403/401 expected on admin/user paths
        sensitive_keywords = ["admin", "/users/", "/account", "/password", "/token", "/secret"]
        if any(kw in request_url.lower() for kw in sensitive_keywords):
            if status == 200 and "error" not in body_lower and "denied" not in body_lower:
                if vuln_class in ("IDOR", "Authorization Bypass", "Authentication Bypass"):
                    return {
                        "indicator": f"Unexpected HTTP {status} on sensitive endpoint",
                        "status_code": status,
                        "confidence": 0.45,
                        "signal_type": "unexpected_success",
                    }

        # Mass assignment: 200/201 with elevated fields in response
        if vuln_class == "Mass Assignment" and status in (200, 201):
            elevated = ["is_admin", "role", "admin", "superuser", "is_staff"]
            if any(f in body_lower for f in elevated):
                return {
                    "indicator": "Elevated field reflected in response",
                    "status_code": status,
                    "confidence": 0.6,
                    "signal_type": "reflected_field",
                }

        return None

    # ─────────────────────────────────────────────────────────
    # Command parsing
    # ─────────────────────────────────────────────────────────

    def _parse_commands(self, rag_output: str) -> list[dict]:
        """Extract test commands from RAG-generated text."""
        commands: list[dict] = []

        # Try JSON array first
        m = re.search(r"\[[\s\S]*?\]", rag_output)
        if m:
            try:
                parsed = json.loads(m.group())
                if isinstance(parsed, list):
                    return [c for c in parsed if isinstance(c, dict)]
            except json.JSONDecodeError:
                pass

        # Fall back to individual JSON objects
        for m in re.finditer(r"\{[\s\S]*?\}", rag_output):
            try:
                obj = json.loads(m.group())
                if isinstance(obj, dict) and ("method" in obj or "url" in obj):
                    commands.append(obj)
            except json.JSONDecodeError:
                continue

        return commands

    # ─────────────────────────────────────────────────────────
    # Finding creation
    # ─────────────────────────────────────────────────────────

    def _make_finding(
        self,
        vuln_class: str,
        description: str,
        url: str,
        method: str,
        headers: dict,
        body: Optional[dict],
        response: dict,
        assessment: dict,
    ) -> Finding:
        profile = VULN_PROFILES.get(vuln_class, {})
        confidence = assessment.get("confidence", 0.5)
        severity = (
            profile.get("severity_high", Severity.MEDIUM)
            if confidence >= 0.7
            else profile.get("severity_low", Severity.LOW)
        )
        cwe = profile.get("cwe")

        # Build RequestRecord
        req_record = RequestRecord(
            method=HttpMethod(method.upper()) if method.upper() in HttpMethod.__members__ else HttpMethod.GET,
            url=url,
            headers=headers,
            body=json.dumps(body) if body else None,
            body_json=body,
            response_status=response.get("status_code", 0),
            response_headers=dict(response.get("headers", {})),
            response_body=response.get("body", "")[:2000],
            response_body_preview=response.get("body", "")[:200],
        )

        step = ReproductionStep(
            step_number=1,
            action=f"{method.upper()} {url}" + (f" with body {json.dumps(body)}" if body else ""),
            expected_result=f"Should reject or return 403 (not vulnerable to {vuln_class})",
            actual_result=(
                f"HTTP {response.get('status_code')} — indicator: {assessment.get('indicator')}"
            ),
        )

        return Finding(
            title=f"[RAG] {vuln_class}: {description[:80]}",
            severity=severity,
            category=TestCategory.RAG,
            asset=url,
            affected_roles=[],
            affected_states=[],
            preconditions=[
                "Target application is accessible",
                f"RAG knowledge base contains {vuln_class} patterns",
            ],
            reproduction_steps=[step],
            request_proof=req_record,
            response_proof=(
                f"HTTP {response.get('status_code')} — "
                f"indicator '{assessment.get('indicator')}' found in response body"
            ),
            reliability_score=confidence * 100,
            root_cause=f"Potential {vuln_class} vulnerability detected by RAG-guided testing",
            impact_types=profile.get("impacts", [ImpactType.CONFIDENTIALITY]),
            cwe_id=cwe,
            raw_evidence={
                "source": "rag_tester",
                "vuln_class": vuln_class,
                "confidence": confidence,
                "signal_type": assessment.get("signal_type"),
                "rag_generated": True,
                "request": {"method": method, "url": url, "headers": headers, "body": body},
                "response": {
                    "status": response.get("status_code"),
                    "body_preview": response.get("body", "")[:500],
                },
            },
        )

    # ─────────────────────────────────────────────────────────
    # RAG prompt generation and execution
    # ─────────────────────────────────────────────────────────

    async def _test_vuln_class(
        self,
        engine: Any,
        vuln_class: str,
        target_url: str,
        recon_summary: str,
        findings_summary: str,
    ) -> list[Finding]:
        """Generate and execute RAG tests for one vulnerability class."""

        prompt = (
            f"You are a penetration tester probing {target_url} for {vuln_class} vulnerabilities.\n\n"
            f"Recon Data:\n{recon_summary}\n\n"
            f"Prior Findings:\n{findings_summary}\n\n"
            f"Using similar vulnerabilities from your knowledge base, generate exactly 3 HTTP requests "
            f"to test for {vuln_class}.\n\n"
            f"Respond with ONLY a JSON array (no extra text). Each element:\n"
            f'{{"method":"GET|POST|PUT|PATCH|DELETE","url":"full URL using {target_url} as base",'
            f'"headers":{{"key":"value"}},"body":null_or_dict,"description":"what this tests",'
            f'"vuln_indicator":"what response pattern means vulnerable"}}\n\n'
            f"Real endpoints from recon (use them): {recon_summary[:300]}"
        )

        try:
            rag_response = engine.generate(
                prompt,
                variables={"query": f"{vuln_class} attack test exploit"},
                n_context=5,
            )
        except Exception as e:
            logger.debug(f"RAG generation [{vuln_class}]: {e}")
            return []

        commands = self._parse_commands(rag_response)
        if not commands:
            logger.debug(f"RAG [{vuln_class}]: no parseable commands in response")
            return []

        findings: list[Finding] = []
        for cmd in commands[:5]:  # cap at 5 requests per vuln class
            url = cmd.get("url", "")
            if not url:
                continue

            # Ensure URL is absolute and within target domain
            if not url.startswith(("http://", "https://")):
                url = target_url.rstrip("/") + "/" + url.lstrip("/")

            # Basic scope check
            try:
                from urllib.parse import urlparse
                target_host = urlparse(target_url).netloc
                cmd_host = urlparse(url).netloc
                if target_host and cmd_host and target_host not in cmd_host:
                    logger.debug(f"RAG: skipping out-of-scope URL {url}")
                    continue
            except Exception:
                pass

            method = cmd.get("method", "GET")
            headers = cmd.get("headers") or {}
            body = cmd.get("body") if isinstance(cmd.get("body"), dict) else None
            description = cmd.get("description", f"{vuln_class} test")

            response = await self._execute_request(method, url, headers, body)
            assessment = self._assess_response(vuln_class, url, response)

            if assessment:
                finding = self._make_finding(
                    vuln_class, description, url, method, headers, body,
                    response, assessment,
                )
                findings.append(finding)
                logger.info(
                    f"RAG Finding: [{vuln_class}] {finding.severity.value} "
                    f"confidence={assessment['confidence']:.0%} @ {url}"
                )

        return findings

    # ─────────────────────────────────────────────────────────
    # Public interface
    # ─────────────────────────────────────────────────────────

    async def run_rag_tests(self) -> list[Finding]:
        """
        Run all RAG-powered vulnerability tests against the target.
        Called by the test runner as the 'rag' category.

        Returns:
            List of findings from RAG-generated test execution
        """
        intel = self._load_intel()
        existing_findings = self._load_existing_findings()
        target_url = (
            self.config.target_url
            or intel.get("_meta", {}).get("target_url", "")
        )

        if not target_url:
            logger.warning("RAG Tester: no target URL — skipping")
            return []

        engine = self._get_engine()
        if engine is None:
            logger.warning("RAG Tester: no LLM engine available — skipping")
            return []

        logger.info(f"RAG Tester: starting {len(VULN_PROFILES)} vulnerability class tests on {target_url}")

        recon_summary = self._build_recon_summary(intel)
        findings_summary = self._build_findings_summary(existing_findings)

        all_findings: list[Finding] = []

        for vuln_class in VULN_PROFILES:
            try:
                found = await self._test_vuln_class(
                    engine, vuln_class, target_url, recon_summary, findings_summary
                )
                all_findings.extend(found)
                # Update findings summary with new finds so next vuln class avoids duplication
                if found:
                    findings_summary += "\n" + self._build_findings_summary(
                        [f.model_dump() for f in found]
                    )
            except Exception as e:
                logger.debug(f"RAG test [{vuln_class}]: {e}")

        self._findings = all_findings
        logger.info(f"RAG Tester: completed — {len(all_findings)} potential findings")
        return all_findings

    async def run_test(self, plan: TestPlan) -> list[Finding]:
        """
        TestRunner-compatible interface. Runs all RAG tests regardless of
        the specific plan (RAG tests are driven by the knowledge base, not
        individual plan items).
        """
        return await self.run_rag_tests()


# ─────────────────────────────────────────────────────────────
# Standalone runner for direct use
# ─────────────────────────────────────────────────────────────

async def run_rag_tester(
    target_url: Optional[str] = None,
    run_id: Optional[str] = None,
) -> list[Finding]:
    """
    Run the RAG tester standalone.

    Args:
        target_url: Override target URL (default: from config/recon)
        run_id: Run ID for output tracking

    Returns:
        List of RAG-discovered findings
    """
    if target_url:
        config = get_config()
        config.target_url = target_url

    tester = RAGTester(run_id=run_id)
    return await tester.run_rag_tests()


if __name__ == "__main__":
    import asyncio
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else None
    findings = asyncio.run(run_rag_tester(target_url=target))
    print(f"\n{'='*60}")
    print(f"RAG Tester complete: {len(findings)} findings")
    for f in findings:
        print(f"  [{f.severity.value.upper()}] {f.title}")
        print(f"    Asset: {f.asset}")
        print(f"    Confidence: {f.reliability_score:.0f}%")
