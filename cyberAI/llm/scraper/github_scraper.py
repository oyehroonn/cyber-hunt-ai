"""
GitHub Security Advisory Scraper

Scrapes public security advisories from GitHub's Advisory Database.
"""

import re
from typing import Optional
from pathlib import Path
from datetime import datetime

import httpx
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class GitHubAdvisoryScraper(BaseScraper):
    """Scraper for GitHub Security Advisories (GHSA)."""
    
    SOURCE_NAME = "github"
    API_BASE = "https://api.github.com"
    ADVISORIES_ENDPOINT = "/advisories"
    REQUEST_DELAY = 1.0
    
    SEVERITY_MAP = {
        "critical": "critical",
        "high": "high",
        "moderate": "medium",
        "medium": "medium",
        "low": "low",
    }
    
    ECOSYSTEM_FILTER = [
        "npm", "pip", "composer", "rubygems", "maven", "nuget",
        "go", "rust", "other"
    ]
    
    WEB_KEYWORDS = [
        "web", "api", "http", "authentication", "authorization", "csrf",
        "xss", "injection", "sqli", "ssrf", "idor", "session", "cookie",
        "jwt", "oauth", "cors", "redirect", "path", "traversal", "upload",
        "deserialization", "rce", "command", "express", "django", "flask",
        "rails", "spring", "laravel", "fastapi", "nextjs", "react",
        "angular", "vue", "graphql", "rest"
    ]
    
    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SecurityResearchBot/1.0",
        }
    
    def _is_web_related(self, advisory) -> bool:
        """Check if advisory is related to web applications."""
        # Skip if not a dict (API response format may vary)
        if not isinstance(advisory, dict):
            return False
        
        try:
            # Check ecosystem
            vulnerabilities = advisory.get("vulnerabilities")
            if isinstance(vulnerabilities, list):
                for vuln in vulnerabilities:
                    if not isinstance(vuln, dict):
                        continue
                    pkg = vuln.get("package")
                    if not isinstance(pkg, dict):
                        continue
                    ecosystem = pkg.get("ecosystem")
                    if isinstance(ecosystem, str) and ecosystem.lower() in ["npm", "pip", "composer", "rubygems"]:
                        return True
            
            # Check keywords in title/description
            summary = advisory.get("summary")
            description = advisory.get("description")
            cwe_ids = advisory.get("cwe_ids")
            
            # Build text safely
            text_parts = []
            if isinstance(summary, str):
                text_parts.append(summary)
            if isinstance(description, str):
                text_parts.append(description)
            if isinstance(cwe_ids, list):
                for c in cwe_ids:
                    if isinstance(c, str):
                        text_parts.append(c)
            
            text = " ".join(text_parts).lower()
            
            return any(kw in text for kw in self.WEB_KEYWORDS)
        except Exception:
            return False
    
    def _fetch_advisories(self, per_page: int = 100, cursor: Optional[str] = None) -> Optional[dict]:
        """Fetch advisories from GitHub API."""
        params = {
            "type": "reviewed",
            "per_page": per_page,
        }
        
        if cursor:
            params["after"] = cursor
        
        try:
            self._rate_limit()
            response = self._get_client().get(
                f"{self.API_BASE}{self.ADVISORIES_ENDPOINT}",
                params=params,
                headers=self.headers,
            )
            
            if response.status_code == 403:
                # Rate limited
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time:
                    wait_time = max(0, int(reset_time) - int(datetime.utcnow().timestamp()))
                    console.print(f"[yellow]Rate limited. Waiting {wait_time}s...[/yellow]")
                    if wait_time < 300:  # Only wait if less than 5 minutes
                        import time
                        time.sleep(wait_time + 1)
                        return self._fetch_advisories(per_page, cursor)
                return None
            
            response.raise_for_status()
            
            # Get pagination cursor from Link header
            link_header = response.headers.get("Link", "")
            next_cursor = None
            if 'rel="next"' in link_header:
                match = re.search(r'after=([^&>]+)', link_header)
                if match:
                    next_cursor = match.group(1)
            
            data = response.json()
            # Handle different API response formats
            if isinstance(data, list):
                advisories = data
            elif isinstance(data, dict):
                # API might return {"data": [...]} or just advisories directly
                advisories = data.get("data", data.get("advisories", []))
                if not isinstance(advisories, list):
                    advisories = [data] if data.get("ghsa_id") else []
            else:
                advisories = []
            
            return {
                "advisories": advisories,
                "next_cursor": next_cursor,
            }
            
        except Exception as e:
            console.print(f"[red]Error fetching advisories: {e}[/red]")
            return None
    
    def _parse_advisory(self, advisory) -> Optional[RawReport]:
        """Parse a GitHub advisory into a RawReport."""
        try:
            # Skip if not a dict
            if not isinstance(advisory, dict):
                return None
            
            ghsa_id = advisory.get("ghsa_id")
            if not ghsa_id or not isinstance(ghsa_id, str):
                return None
            
            # Check if already scraped
            if self._report_exists(ghsa_id):
                return None
            
            # Extract severity safely
            severity_raw = advisory.get("severity")
            severity = self.SEVERITY_MAP.get(
                str(severity_raw).lower() if severity_raw else "",
                "medium"
            )
            
            # Extract CVE info safely
            cve_ids = advisory.get("cve_id")
            cve = None
            if isinstance(cve_ids, list) and cve_ids:
                cve = str(cve_ids[0]) if cve_ids[0] else None
            elif isinstance(cve_ids, str):
                cve = cve_ids
            
            # Extract CWE safely
            cwe_ids = advisory.get("cwe_ids")
            cwe = None
            if isinstance(cwe_ids, list) and cwe_ids:
                first_cwe = cwe_ids[0]
                cwe = str(first_cwe) if first_cwe and isinstance(first_cwe, str) else None
            
            # Extract CVSS safely
            cvss = advisory.get("cvss")
            cvss_score = None
            cvss_vector = None
            if isinstance(cvss, dict):
                cvss_score = cvss.get("score")
                cvss_vector = cvss.get("vector_string")
            
            # Extract affected packages safely
            vulnerabilities = advisory.get("vulnerabilities")
            affected = []
            if isinstance(vulnerabilities, list):
                for vuln in vulnerabilities:
                    if not isinstance(vuln, dict):
                        continue
                    pkg = vuln.get("package")
                    if not isinstance(pkg, dict):
                        continue
                    pkg_name = pkg.get("name", "")
                    ecosystem = pkg.get("ecosystem", "")
                    if pkg_name and isinstance(pkg_name, str):
                        affected.append(f"{ecosystem}:{pkg_name}")
            
            # Determine vulnerability type from CWE or description
            vuln_type = self._determine_vuln_type(advisory, cwe)
            
            # Build description from summary and description safely
            description = advisory.get("summary") or ""
            body = advisory.get("description") or ""
            if not isinstance(description, str):
                description = str(description) if description else ""
            if not isinstance(body, str):
                body = str(body) if body else ""
            
            # Get title safely
            title = advisory.get("summary")
            if not title or not isinstance(title, str):
                title = f"GHSA: {ghsa_id}"
            
            # Get URL safely
            url = advisory.get("html_url")
            if not url or not isinstance(url, str):
                url = f"https://github.com/advisories/{ghsa_id}"
            
            # Extract references safely
            references_raw = advisory.get("references")
            references = []
            if isinstance(references_raw, list):
                for r in references_raw:
                    if isinstance(r, dict):
                        ref_url = r.get("url")
                        if ref_url and isinstance(ref_url, str):
                            references.append(ref_url)
            
            # Extract credits safely
            credits_raw = advisory.get("credits")
            credits = []
            if isinstance(credits_raw, list):
                for c in credits_raw:
                    if isinstance(c, dict):
                        user = c.get("user")
                        if isinstance(user, dict):
                            login = user.get("login")
                            if login and isinstance(login, str):
                                credits.append(login)
            
            report = RawReport(
                id=ghsa_id,
                source=self.SOURCE_NAME,
                title=title,
                url=url,
                severity=severity,
                vuln_type=vuln_type,
                cwe=cwe,
                cvss_score=cvss_score,
                affected_component=", ".join(affected[:3]) if affected else None,
                description=description,
                body=body,
                disclosed_at=advisory.get("published_at"),
                metadata={
                    "ghsa_id": ghsa_id,
                    "cve_id": cve,
                    "cwe_ids": cwe_ids if isinstance(cwe_ids, list) else [],
                    "cvss_vector": cvss_vector,
                    "affected_packages": affected,
                    "references": references,
                    "credits": credits,
                }
            )
            
            return report
            
        except Exception as e:
            console.print(f"[dim]Error parsing advisory {type(advisory).__name__}: {e}[/dim]")
            return None
    
    def _determine_vuln_type(self, advisory, cwe: Optional[str]) -> Optional[str]:
        """Determine vulnerability type from advisory content."""
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
            "CWE-1321": "Prototype Pollution",
            "CWE-400": "DoS",
            "CWE-20": "Input Validation",
        }
        
        if cwe and isinstance(cwe, str) and cwe in CWE_TO_VULN:
            return CWE_TO_VULN[cwe]
        
        # Check text content safely
        try:
            if not isinstance(advisory, dict):
                return None
            
            summary = advisory.get("summary")
            description = advisory.get("description")
            
            text_parts = []
            if isinstance(summary, str):
                text_parts.append(summary)
            if isinstance(description, str):
                text_parts.append(description)
            
            text = " ".join(text_parts).lower()
            
            patterns = [
                (r"cross.?site.?script|xss", "XSS"),
                (r"sql.?inject", "SQL Injection"),
                (r"csrf|cross.?site.?request.?forgery", "CSRF"),
                (r"ssrf|server.?side.?request", "SSRF"),
                (r"xxe|xml.?external", "XXE"),
                (r"path.?traversal|directory.?traversal", "Path Traversal"),
                (r"command.?inject|os.?command", "Command Injection"),
                (r"auth.?bypass", "Authentication Bypass"),
                (r"access.?control|authorization", "Broken Access Control"),
                (r"idor|insecure.?direct.?object", "IDOR"),
                (r"deserializ", "Insecure Deserialization"),
                (r"prototype.?pollution", "Prototype Pollution"),
                (r"open.?redirect", "Open Redirect"),
                (r"remote.?code|rce", "RCE"),
            ]
            
            for pattern, vuln_type in patterns:
                if re.search(pattern, text):
                    return vuln_type
        except Exception:
            pass
        
        return None
    
    def scrape(self, max_reports: int = 30, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape GitHub Security Advisories.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        cursor = None
        pages_fetched = 0
        max_pages = 5  # GitHub returns up to 100 per page
        
        console.print(f"[cyan]Scraping GitHub Security Advisories (target: {max_reports} reports)...[/cyan]")
        
        while len(reports) < max_reports and pages_fetched < max_pages:
            result = self._fetch_advisories(per_page=100, cursor=cursor)
            
            if not result:
                break
            
            advisories = result.get("advisories", [])
            if not advisories:
                break
            
            for advisory in advisories:
                if len(reports) >= max_reports:
                    break
                
                try:
                    # Filter for web-related advisories
                    if not self._is_web_related(advisory):
                        continue
                    
                    report = self._parse_advisory(advisory)
                    if report:
                        self._save_report(report)
                        reports.append(report)
                        
                        if progress and task:
                            progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"[dim]Error processing advisory: {e}[/dim]")
            
            cursor = result.get("next_cursor")
            if not cursor:
                break
            
            pages_fetched += 1
        
        console.print(f"[green]Scraped {len(reports)} new GitHub advisories[/green]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with GitHubAdvisoryScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=10)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title} ({r.severity})")
