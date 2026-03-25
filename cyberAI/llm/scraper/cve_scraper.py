"""
CVE/NVD Scraper

Scrapes vulnerability information from NIST National Vulnerability Database (NVD).
"""

import re
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
import time

import httpx
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class CVEScraper(BaseScraper):
    """Scraper for CVE entries from NVD."""
    
    SOURCE_NAME = "cve"
    NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    REQUEST_DELAY = 6.0  # NVD requires 6 second delay without API key
    
    SEVERITY_MAP = {
        "CRITICAL": "critical",
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
    }
    
    WEB_KEYWORDS = [
        "web application", "api", "http", "authentication bypass",
        "authorization", "csrf", "xss", "sql injection", "ssrf",
        "idor", "session", "cookie", "jwt", "oauth", "cors",
        "open redirect", "path traversal", "file upload",
        "deserialization", "command injection", "remote code execution",
        "privilege escalation", "access control", "graphql", "rest api"
    ]
    
    SEARCH_QUERIES = [
        "web authentication bypass",
        "web api authorization",
        "IDOR insecure direct object",
        "SSRF server side request forgery",
        "business logic vulnerability",
        "race condition web",
        "access control bypass",
        "SQL injection web application",
        "cross site scripting XSS",
        "CSRF cross site request forgery",
        "JWT token vulnerability",
        "OAuth bypass",
        "session fixation",
        "path traversal web",
        "file upload vulnerability",
        "deserialization vulnerability",
        "command injection web",
    ]
    
    def __init__(self, data_dir: Path, api_key: Optional[str] = None):
        super().__init__(data_dir)
        self.api_key = api_key
        if api_key:
            self.REQUEST_DELAY = 0.6  # With API key, can go faster
    
    def _build_api_headers(self) -> dict:
        """Build API headers including API key if available."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "SecurityResearchBot/1.0",
        }
        if self.api_key:
            headers["apiKey"] = self.api_key
        return headers
    
    def _fetch_cves(self, keyword_search: str, results_per_page: int = 50,
                    start_index: int = 0) -> Optional[dict]:
        """Fetch CVEs matching keyword search."""
        params = {
            "keywordSearch": keyword_search,
            "resultsPerPage": min(results_per_page, 100),
            "startIndex": start_index,
        }
        
        try:
            self._rate_limit()
            response = self._get_client().get(
                self.NVD_API_BASE,
                params=params,
                headers=self._build_api_headers(),
                timeout=60.0,
            )
            
            if response.status_code == 403:
                console.print("[yellow]NVD rate limit reached. Waiting...[/yellow]")
                time.sleep(30)
                return self._fetch_cves(keyword_search, results_per_page, start_index)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            console.print(f"[red]Error fetching CVEs: {e}[/red]")
            return None
    
    def _fetch_recent_cves(self, days_back: int = 90, results_per_page: int = 100) -> Optional[dict]:
        """Fetch recent CVEs modified in the last N days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "lastModStartDate": start_date.strftime("%Y-%m-%dT00:00:00.000"),
            "lastModEndDate": end_date.strftime("%Y-%m-%dT23:59:59.999"),
            "resultsPerPage": min(results_per_page, 100),
        }
        
        try:
            self._rate_limit()
            response = self._get_client().get(
                self.NVD_API_BASE,
                params=params,
                headers=self._build_api_headers(),
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[dim]Error fetching recent CVEs: {e}[/dim]")
            return None
    
    def _is_web_related(self, cve_item: dict) -> bool:
        """Check if CVE is related to web applications."""
        cve = cve_item.get("cve", {})
        
        # Check descriptions
        descriptions = cve.get("descriptions", [])
        for desc in descriptions:
            text = desc.get("value", "").lower()
            if any(kw in text for kw in self.WEB_KEYWORDS):
                return True
        
        # Check CWE
        weaknesses = cve.get("weaknesses", [])
        WEB_CWES = {
            "CWE-79", "CWE-89", "CWE-352", "CWE-918", "CWE-611",
            "CWE-22", "CWE-78", "CWE-287", "CWE-284", "CWE-639",
            "CWE-200", "CWE-502", "CWE-362", "CWE-601", "CWE-94",
            "CWE-434", "CWE-306", "CWE-269", "CWE-863", "CWE-862"
        }
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                cwe = desc.get("value", "")
                if cwe in WEB_CWES:
                    return True
        
        return False
    
    def _parse_cve(self, cve_item: dict) -> Optional[RawReport]:
        """Parse a CVE item into a RawReport."""
        try:
            cve = cve_item.get("cve", {})
            cve_id = cve.get("id")
            
            if not cve_id:
                return None
            
            # Check if already scraped
            if self._report_exists(cve_id):
                return None
            
            # Extract description
            descriptions = cve.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            if not description and descriptions:
                description = descriptions[0].get("value", "")
            
            # Extract severity and CVSS
            metrics = cve.get("metrics", {})
            cvss_score = None
            severity = "medium"
            
            # Try CVSS 3.1 first
            cvss31 = metrics.get("cvssMetricV31", [])
            if cvss31:
                cvss_data = cvss31[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                severity = self.SEVERITY_MAP.get(
                    cvss_data.get("baseSeverity", "").upper(),
                    "medium"
                )
            else:
                # Try CVSS 3.0
                cvss30 = metrics.get("cvssMetricV30", [])
                if cvss30:
                    cvss_data = cvss30[0].get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore")
                    severity = self.SEVERITY_MAP.get(
                        cvss_data.get("baseSeverity", "").upper(),
                        "medium"
                    )
                else:
                    # Try CVSS 2.0
                    cvss2 = metrics.get("cvssMetricV2", [])
                    if cvss2:
                        cvss_data = cvss2[0].get("cvssData", {})
                        cvss_score = cvss_data.get("baseScore")
                        # Map CVSS 2.0 score to severity
                        if cvss_score:
                            if cvss_score >= 9.0:
                                severity = "critical"
                            elif cvss_score >= 7.0:
                                severity = "high"
                            elif cvss_score >= 4.0:
                                severity = "medium"
                            else:
                                severity = "low"
            
            # Extract CWE
            cwe = None
            weaknesses = cve.get("weaknesses", [])
            for weakness in weaknesses:
                for desc in weakness.get("description", []):
                    cwe_value = desc.get("value", "")
                    if cwe_value.startswith("CWE-"):
                        cwe = cwe_value
                        break
                if cwe:
                    break
            
            # Determine vulnerability type
            vuln_type = self._determine_vuln_type(description, cwe)
            
            # Extract references
            references = cve.get("references", [])
            ref_urls = [r.get("url") for r in references[:10]]
            
            # Build affected component from configurations
            configurations = cve.get("configurations", [])
            affected = []
            for config in configurations[:3]:
                for node in config.get("nodes", [])[:3]:
                    for match in node.get("cpeMatch", [])[:3]:
                        criteria = match.get("criteria", "")
                        if criteria:
                            parts = criteria.split(":")
                            if len(parts) >= 5:
                                affected.append(f"{parts[3]}:{parts[4]}")
            
            report = RawReport(
                id=cve_id,
                source=self.SOURCE_NAME,
                title=f"{cve_id}: {description[:100]}..." if len(description) > 100 else f"{cve_id}: {description}",
                url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                severity=severity,
                vuln_type=vuln_type,
                cwe=cwe,
                cvss_score=cvss_score,
                affected_component=", ".join(affected[:3]) if affected else None,
                description=description,
                body=description,
                disclosed_at=cve.get("published"),
                metadata={
                    "cve_id": cve_id,
                    "references": ref_urls,
                    "configurations": affected,
                    "source_identifier": cve.get("sourceIdentifier"),
                    "vuln_status": cve.get("vulnStatus"),
                }
            )
            
            return report
            
        except Exception as e:
            console.print(f"[dim]Error parsing CVE: {e}[/dim]")
            return None
    
    def _determine_vuln_type(self, description: str, cwe: Optional[str]) -> Optional[str]:
        """Determine vulnerability type from description and CWE."""
        CWE_TO_VULN = {
            "CWE-79": "XSS",
            "CWE-89": "SQL Injection",
            "CWE-352": "CSRF",
            "CWE-918": "SSRF",
            "CWE-611": "XXE",
            "CWE-22": "Path Traversal",
            "CWE-78": "Command Injection",
            "CWE-77": "Command Injection",
            "CWE-287": "Authentication Bypass",
            "CWE-284": "Broken Access Control",
            "CWE-639": "IDOR",
            "CWE-200": "Information Disclosure",
            "CWE-502": "Insecure Deserialization",
            "CWE-362": "Race Condition",
            "CWE-601": "Open Redirect",
            "CWE-94": "Code Injection",
            "CWE-434": "Unrestricted File Upload",
            "CWE-306": "Missing Authentication",
            "CWE-269": "Privilege Escalation",
            "CWE-863": "Authorization Bypass",
            "CWE-862": "Missing Authorization",
        }
        
        if cwe and cwe in CWE_TO_VULN:
            return CWE_TO_VULN[cwe]
        
        text = description.lower()
        patterns = [
            (r"cross.?site.?script|xss", "XSS"),
            (r"sql.?inject", "SQL Injection"),
            (r"csrf|cross.?site.?request.?forg", "CSRF"),
            (r"ssrf|server.?side.?request", "SSRF"),
            (r"xxe|xml.?external", "XXE"),
            (r"path.?traversal|directory.?traversal", "Path Traversal"),
            (r"command.?inject|os.?command", "Command Injection"),
            (r"auth.?bypass", "Authentication Bypass"),
            (r"access.?control|authorization.?bypass", "Broken Access Control"),
            (r"idor|insecure.?direct.?object", "IDOR"),
            (r"deserializ", "Insecure Deserialization"),
            (r"file.?upload", "Unrestricted File Upload"),
            (r"open.?redirect", "Open Redirect"),
            (r"remote.?code|rce", "RCE"),
            (r"privilege.?escalat", "Privilege Escalation"),
            (r"information.?disclos|info.?leak", "Information Disclosure"),
        ]
        
        for pattern, vuln_type in patterns:
            if re.search(pattern, text):
                return vuln_type
        
        return None
    
    def scrape(self, max_reports: int = 30, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape CVEs from NVD.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        
        console.print(f"[cyan]Scraping NVD CVE database (target: {max_reports} CVEs)...[/cyan]")
        console.print("[dim]Note: NVD API requires 6 second delay between requests without API key[/dim]")
        
        # Search for web-related CVEs using different keywords
        for query in self.SEARCH_QUERIES:
            if len(reports) >= max_reports:
                break
            
            console.print(f"[dim]Searching: {query}[/dim]")
            result = self._fetch_cves(query, results_per_page=50)
            
            if not result:
                continue
            
            vulnerabilities = result.get("vulnerabilities", [])
            
            for vuln in vulnerabilities:
                if len(reports) >= max_reports:
                    break
                
                # Extra filter for web-related
                if not self._is_web_related(vuln):
                    continue
                
                report = self._parse_cve(vuln)
                if report:
                    self._save_report(report)
                    reports.append(report)
                    
                    if progress and task:
                        progress.update(task, advance=1)
        
        console.print(f"[green]Scraped {len(reports)} new CVEs[/green]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    import os
    
    data_dir = Path(__file__).parent.parent / "data"
    api_key = os.environ.get("NVD_API_KEY")
    
    with CVEScraper(data_dir, api_key=api_key) as scraper:
        reports = scraper.scrape(max_reports=5)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title[:80]}... ({r.severity})")
