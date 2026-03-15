"""
Step 14: Security Controls - Security header and control analysis.
Analyzes CSP, CORS, CSRF, cookies, and other security controls.
"""

import re
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.models import RequestRecord, SecurityControl, SecurityControlsReport
from cyberAI.utils.helpers import (
    add_meta_to_output,
    atomic_write_json,
    generate_run_id,
)


class SecurityControlsAnalyzer:
    """
    Analyzes security controls from response headers and behavior.
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.config = get_config()
        self.run_id = run_id or generate_run_id()
        self._controls: list[SecurityControl] = []
        self._csp_policy: Optional[str] = None
        self._cors_origins: list[str] = []
        self._csrf_mechanism: Optional[str] = None
        self._token_storage: Optional[str] = None
        self._cookie_analysis: dict[str, dict] = {}
    
    def _parse_csp(self, csp_header: str) -> dict[str, list[str]]:
        """Parse CSP header into directives."""
        directives = {}
        
        for directive in csp_header.split(';'):
            directive = directive.strip()
            if not directive:
                continue
            
            parts = directive.split()
            if parts:
                name = parts[0]
                values = parts[1:] if len(parts) > 1 else []
                directives[name] = values
        
        return directives
    
    def _analyze_csp(self, csp_header: str) -> SecurityControl:
        """Analyze CSP for weaknesses."""
        is_weak = False
        weakness_reasons = []
        
        directives = self._parse_csp(csp_header)
        
        dangerous_sources = ["'unsafe-inline'", "'unsafe-eval'", "*", "data:"]
        
        for directive, values in directives.items():
            for source in dangerous_sources:
                if source in values:
                    is_weak = True
                    weakness_reasons.append(f"{directive} allows {source}")
        
        if "default-src" not in directives and "script-src" not in directives:
            is_weak = True
            weakness_reasons.append("Missing default-src or script-src")
        
        self._csp_policy = csp_header
        
        return SecurityControl(
            control_type="csp",
            present=True,
            value=csp_header[:500],
            is_weak=is_weak,
            weakness_reason="; ".join(weakness_reasons) if weakness_reasons else None,
        )
    
    def _analyze_cors(self, headers: dict) -> SecurityControl:
        """Analyze CORS configuration."""
        acao = headers.get("access-control-allow-origin", "")
        acac = headers.get("access-control-allow-credentials", "")
        
        is_weak = False
        weakness_reasons = []
        
        if acao == "*":
            is_weak = True
            weakness_reasons.append("Allows all origins")
            
            if acac.lower() == "true":
                is_weak = True
                weakness_reasons.append("Allows credentials with wildcard origin")
        
        if acao:
            self._cors_origins.append(acao)
        
        return SecurityControl(
            control_type="cors",
            present=bool(acao),
            value=acao,
            is_weak=is_weak,
            weakness_reason="; ".join(weakness_reasons) if weakness_reasons else None,
        )
    
    def _analyze_cookie(self, cookie_header: str, cookie_name: str) -> dict:
        """Analyze cookie security attributes."""
        analysis = {
            "name": cookie_name,
            "secure": False,
            "httponly": False,
            "samesite": None,
            "is_weak": False,
            "weaknesses": [],
        }
        
        attrs_lower = cookie_header.lower()
        
        if "secure" in attrs_lower:
            analysis["secure"] = True
        else:
            analysis["is_weak"] = True
            analysis["weaknesses"].append("Missing Secure flag")
        
        if "httponly" in attrs_lower:
            analysis["httponly"] = True
        else:
            if any(s in cookie_name.lower() for s in ["session", "token", "auth"]):
                analysis["is_weak"] = True
                analysis["weaknesses"].append("Missing HttpOnly flag on sensitive cookie")
        
        samesite_match = re.search(r'samesite\s*=\s*(strict|lax|none)', attrs_lower)
        if samesite_match:
            analysis["samesite"] = samesite_match.group(1)
            if analysis["samesite"] == "none" and not analysis["secure"]:
                analysis["is_weak"] = True
                analysis["weaknesses"].append("SameSite=None without Secure")
        else:
            analysis["is_weak"] = True
            analysis["weaknesses"].append("Missing SameSite attribute")
        
        return analysis
    
    def _detect_csrf_mechanism(self, record: RequestRecord) -> Optional[str]:
        """Detect CSRF protection mechanism from request."""
        csrf_headers = ["x-csrf-token", "x-xsrf-token", "csrf-token", "_csrf"]
        
        for header in csrf_headers:
            if header in record.headers or header.upper() in record.headers:
                return "header"
        
        if record.body_json:
            csrf_fields = ["_csrf", "csrf_token", "csrfToken", "_token"]
            for field in csrf_fields:
                if field in record.body_json:
                    return "form_field"
        
        if record.cookies:
            csrf_cookies = ["csrf", "xsrf", "_csrf"]
            for cookie in record.cookies:
                if any(c in cookie.lower() for c in csrf_cookies):
                    return "double_submit"
        
        return None
    
    def _detect_token_storage(self, js_content: Optional[str] = None) -> Optional[str]:
        """Detect token storage mechanism from JS analysis."""
        if not js_content:
            return None
        
        if "localStorage" in js_content and ("token" in js_content.lower() or "jwt" in js_content.lower()):
            return "localStorage"
        elif "sessionStorage" in js_content and ("token" in js_content.lower() or "jwt" in js_content.lower()):
            return "sessionStorage"
        
        return "httpOnly_cookie"
    
    def process_response(self, record: RequestRecord) -> list[SecurityControl]:
        """
        Process a response to extract security controls.
        
        Args:
            record: Request record to process
            
        Returns:
            List of SecurityControl objects discovered
        """
        controls = []
        headers_lower = {k.lower(): v for k, v in record.response_headers.items()}
        
        csp = headers_lower.get("content-security-policy")
        if csp:
            controls.append(self._analyze_csp(csp))
        else:
            controls.append(SecurityControl(
                control_type="csp",
                present=False,
                is_weak=True,
                weakness_reason="Missing CSP header",
            ))
        
        if "access-control-allow-origin" in headers_lower:
            controls.append(self._analyze_cors(headers_lower))
        
        hsts = headers_lower.get("strict-transport-security")
        if hsts:
            is_weak = False
            weakness = None
            
            max_age_match = re.search(r'max-age\s*=\s*(\d+)', hsts)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                if max_age < 31536000:
                    is_weak = True
                    weakness = f"max-age too short ({max_age}s, should be >= 1 year)"
            
            controls.append(SecurityControl(
                control_type="hsts",
                present=True,
                value=hsts,
                is_weak=is_weak,
                weakness_reason=weakness,
            ))
        else:
            controls.append(SecurityControl(
                control_type="hsts",
                present=False,
                is_weak=True,
                weakness_reason="Missing HSTS header",
            ))
        
        x_frame = headers_lower.get("x-frame-options")
        controls.append(SecurityControl(
            control_type="x_frame_options",
            present=bool(x_frame),
            value=x_frame,
            is_weak=not x_frame,
            weakness_reason="Missing X-Frame-Options" if not x_frame else None,
        ))
        
        x_content_type = headers_lower.get("x-content-type-options")
        controls.append(SecurityControl(
            control_type="x_content_type_options",
            present=bool(x_content_type),
            value=x_content_type,
            is_weak=x_content_type != "nosniff" if x_content_type else True,
        ))
        
        set_cookies = headers_lower.get("set-cookie", "")
        if set_cookies:
            cookie_name = set_cookies.split("=")[0] if "=" in set_cookies else "unknown"
            cookie_analysis = self._analyze_cookie(set_cookies, cookie_name)
            self._cookie_analysis[cookie_name] = cookie_analysis
            
            controls.append(SecurityControl(
                control_type="cookie_flags",
                present=True,
                value=f"{cookie_name}: Secure={cookie_analysis['secure']}, HttpOnly={cookie_analysis['httponly']}, SameSite={cookie_analysis['samesite']}",
                is_weak=cookie_analysis["is_weak"],
                weakness_reason="; ".join(cookie_analysis["weaknesses"]) if cookie_analysis["weaknesses"] else None,
            ))
        
        csrf = self._detect_csrf_mechanism(record)
        if csrf:
            self._csrf_mechanism = csrf
            controls.append(SecurityControl(
                control_type="csrf",
                present=True,
                value=csrf,
            ))
        elif record.method.value in ("POST", "PUT", "PATCH", "DELETE"):
            controls.append(SecurityControl(
                control_type="csrf",
                present=False,
                is_weak=True,
                weakness_reason="No CSRF protection detected on state-changing endpoint",
                affected_endpoints=[record.url],
            ))
        
        rate_limit_headers = ["x-ratelimit-limit", "x-rate-limit-limit", "retry-after"]
        has_rate_limit = any(h in headers_lower for h in rate_limit_headers)
        controls.append(SecurityControl(
            control_type="rate_limit",
            present=has_rate_limit,
            is_weak=not has_rate_limit,
            weakness_reason="No rate limiting headers detected" if not has_rate_limit else None,
        ))
        
        return controls
    
    def process_requests_batch(self, requests: list[RequestRecord]) -> None:
        """
        Process a batch of requests.
        
        Args:
            requests: List of request records
        """
        seen_controls = set()
        
        for record in requests:
            controls = self.process_response(record)
            
            for control in controls:
                key = (control.control_type, control.value)
                if key not in seen_controls:
                    seen_controls.add(key)
                    self._controls.append(control)
    
    def get_report(self) -> SecurityControlsReport:
        """
        Generate security controls report.
        
        Returns:
            SecurityControlsReport object
        """
        missing = [c.control_type for c in self._controls if not c.present]
        weak = [c.control_type for c in self._controls if c.is_weak]
        
        return SecurityControlsReport(
            controls=self._controls,
            csp_policy=self._csp_policy,
            cors_origins=list(set(self._cors_origins)),
            csrf_mechanism=self._csrf_mechanism,
            token_storage=self._token_storage,
            missing_controls=list(set(missing)),
            weak_controls=list(set(weak)),
        )
    
    def save_report(self) -> str:
        """
        Save security controls report.
        
        Returns:
            Path to saved file
        """
        report = self.get_report()
        
        output_path = self.config.get_output_path(
            "recon", "intelligence", "security_controls.json"
        )
        
        data = add_meta_to_output(
            {
                "report": report.model_dump(),
                "cookie_analysis": self._cookie_analysis,
                "summary": {
                    "total_controls_checked": len(self._controls),
                    "missing_controls": len(report.missing_controls),
                    "weak_controls": len(report.weak_controls),
                },
            },
            target_url=self.config.target_url,
            phase="recon",
            run_id=self.run_id,
        )
        
        atomic_write_json(output_path, data)
        logger.info(f"Saved security controls report")
        
        return str(output_path)


def run_security_controls_analysis(
    requests: list[RequestRecord],
    run_id: Optional[str] = None,
) -> SecurityControlsAnalyzer:
    """
    Run security controls analysis.
    
    Args:
        requests: Captured requests
        run_id: Run ID
        
    Returns:
        SecurityControlsAnalyzer instance with results
    """
    analyzer = SecurityControlsAnalyzer(run_id=run_id)
    analyzer.process_requests_batch(requests)
    analyzer.save_report()
    return analyzer


if __name__ == "__main__":
    from cyberAI.models import HttpMethod
    
    analyzer = SecurityControlsAnalyzer()
    
    record = RequestRecord(
        method=HttpMethod.GET,
        url="https://example.com/api/data",
        headers={},
        response_status=200,
        response_headers={
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Access-Control-Allow-Origin": "*",
            "Set-Cookie": "session=abc123; Secure; HttpOnly; SameSite=Strict",
        },
    )
    
    analyzer.process_requests_batch([record])
    analyzer.save_report()
    
    report = analyzer.get_report()
    print(f"Missing controls: {report.missing_controls}")
    print(f"Weak controls: {report.weak_controls}")
