"""
PayloadsAllTheThings Scraper

Scrapes security payloads and techniques from PayloadsAllTheThings GitHub repository.
"""

import re
from typing import Optional
from pathlib import Path

from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class PayloadsScraper(BaseScraper):
    """Scraper for PayloadsAllTheThings content."""
    
    SOURCE_NAME = "payloads"
    BASE_URL = "https://swisskyrepo.github.io/PayloadsAllTheThings"
    RAW_GITHUB_BASE = "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master"
    REQUEST_DELAY = 1.0
    
    # Categories to scrape with their vulnerability types and CWEs
    CATEGORIES = [
        ("SQL Injection", "SQL Injection", "CWE-89", "high"),
        ("XSS Injection", "XSS", "CWE-79", "high"),
        ("CSRF Injection", "CSRF", "CWE-352", "high"),
        ("Server Side Request Forgery", "SSRF", "CWE-918", "high"),
        ("XXE Injection", "XXE", "CWE-611", "high"),
        ("Command Injection", "Command Injection", "CWE-78", "critical"),
        ("Directory Traversal", "Path Traversal", "CWE-22", "high"),
        ("File Inclusion", "File Inclusion", "CWE-98", "high"),
        ("Insecure Deserialization", "Insecure Deserialization", "CWE-502", "critical"),
        ("LDAP Injection", "LDAP Injection", "CWE-90", "high"),
        ("NoSQL Injection", "NoSQL Injection", "CWE-943", "high"),
        ("XPATH Injection", "XPATH Injection", "CWE-643", "high"),
        ("IDOR Insecure Direct Object References", "IDOR", "CWE-639", "high"),
        ("OAuth Misconfiguration", "OAuth Vulnerabilities", "CWE-287", "high"),
        ("Open Redirect", "Open Redirect", "CWE-601", "medium"),
        ("SSTI Injection", "Template Injection", "CWE-94", "critical"),
        ("Upload Insecure Files", "File Upload", "CWE-434", "critical"),
        ("Web Cache Deception", "Web Cache Deception", None, "medium"),
        ("CRLF Injection", "CRLF Injection", "CWE-93", "medium"),
        ("CSV Injection", "CSV Injection", "CWE-1236", "medium"),
        ("HTTP Parameter Pollution", "HTTP Parameter Pollution", None, "medium"),
        ("Race Condition", "Race Condition", "CWE-362", "high"),
        ("Request Smuggling", "HTTP Request Smuggling", "CWE-444", "high"),
        ("Prototype Pollution", "Prototype Pollution", "CWE-1321", "high"),
        ("GraphQL Injection", "GraphQL Vulnerabilities", None, "high"),
        ("JWT Security", "JWT Vulnerabilities", "CWE-347", "high"),
        ("Mass Assignment", "Mass Assignment", "CWE-915", "high"),
        ("Business Logic", "Business Logic", "CWE-840", "high"),
    ]
    
    def _fetch_category_page(self, category: str) -> Optional[str]:
        """Fetch a category page from the documentation site."""
        # Try the GitHub Pages site first
        url_slug = category.replace(" ", "%20")
        url = f"{self.BASE_URL}/{url_slug}/"
        
        response = self._fetch_with_retry(url)
        if response and response.status_code == 200:
            return response.text
        
        # Try alternative URL format
        url_slug_alt = category.replace(" ", "-").lower()
        url = f"{self.BASE_URL}/{url_slug_alt}/"
        
        response = self._fetch_with_retry(url)
        if response and response.status_code == 200:
            return response.text
        
        return None
    
    def _fetch_raw_readme(self, category: str) -> Optional[str]:
        """Fetch raw README.md from GitHub."""
        # Try different path formats
        paths_to_try = [
            f"{self.RAW_GITHUB_BASE}/{category}/README.md",
            f"{self.RAW_GITHUB_BASE}/{category.replace(' ', '%20')}/README.md",
        ]
        
        for path in paths_to_try:
            response = self._fetch_with_retry(path)
            if response and response.status_code == 200:
                return response.text
        
        return None
    
    def _parse_markdown_content(self, content: str, category: str, 
                                vuln_type: str, cwe: Optional[str], 
                                severity: str) -> Optional[RawReport]:
        """Parse markdown content into a RawReport."""
        if not content or len(content) < 100:
            return None
        
        # Extract title from first heading
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else category
        title = f"PayloadsAllTheThings: {title}"
        
        # Clean up content - remove badges, TOC links
        content = re.sub(r"\[!\[.+?\]\(.+?\)\]\(.+?\)", "", content)  # badges
        content = re.sub(r"\[\[_TOC_\]\]", "", content)  # TOC markers
        
        # Extract sections
        sections = {}
        current_section = "intro"
        current_content = []
        
        for line in content.split("\n"):
            if re.match(r"^##?\s+", line):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = re.sub(r"^##?\s+", "", line).strip().lower()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        # Build structured body
        body_parts = []
        
        # Add introduction
        if "intro" in sections:
            body_parts.append(sections["intro"])
        
        # Add exploitation techniques
        for key in sections:
            if any(term in key for term in ["exploit", "payload", "bypass", "example", "attack"]):
                body_parts.append(f"\n## {key.title()}\n{sections[key]}")
        
        # Add detection/prevention if available
        for key in sections:
            if any(term in key for term in ["detect", "prevent", "mitigat", "fix", "remediat"]):
                body_parts.append(f"\n## {key.title()}\n{sections[key]}")
        
        body = "\n".join(body_parts)
        
        # If body is too short, use full content
        if len(body) < 200:
            body = content
        
        # Truncate if too long
        body = body[:10000]
        
        report_id = self._generate_id(f"payloads_{category}")
        
        report = RawReport(
            id=report_id,
            source=self.SOURCE_NAME,
            title=title,
            url=f"{self.BASE_URL}/{category.replace(' ', '%20')}/",
            severity=severity,
            vuln_type=vuln_type,
            cwe=cwe,
            description=content[:500],
            body=body,
            metadata={
                "category": category,
                "source_repo": "swisskyrepo/PayloadsAllTheThings",
                "sections": list(sections.keys())[:10],
            }
        )
        
        return report
    
    def _parse_html_page(self, html: str, category: str,
                         vuln_type: str, cwe: Optional[str],
                         severity: str) -> Optional[RawReport]:
        """Parse HTML page into a RawReport."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove navigation elements
            for elem in soup.find_all(["nav", "footer", "aside"]):
                elem.decompose()
            
            # Extract title
            title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else category
            title = f"PayloadsAllTheThings: {title}"
            
            # Extract main content
            main = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content|markdown"))
            
            if not main:
                return None
            
            body = main.get_text(separator="\n", strip=True)
            
            if len(body) < 100:
                return None
            
            report_id = self._generate_id(f"payloads_{category}")
            
            report = RawReport(
                id=report_id,
                source=self.SOURCE_NAME,
                title=title,
                url=f"{self.BASE_URL}/{category.replace(' ', '%20')}/",
                severity=severity,
                vuln_type=vuln_type,
                cwe=cwe,
                description=body[:500],
                body=body[:10000],
                metadata={
                    "category": category,
                    "source_repo": "swisskyrepo/PayloadsAllTheThings",
                }
            )
            
            return report
            
        except Exception as e:
            console.print(f"[dim]Error parsing HTML for {category}: {e}[/dim]")
            return None
    
    def scrape(self, max_reports: int = 30, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape PayloadsAllTheThings content.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        
        console.print(f"[cyan]Scraping PayloadsAllTheThings (target: {max_reports} entries)...[/cyan]")
        
        for category, vuln_type, cwe, severity in self.CATEGORIES:
            if len(reports) >= max_reports:
                break
            
            report_id = self._generate_id(f"payloads_{category}")
            
            if self._report_exists(report_id):
                if progress and task:
                    progress.update(task, advance=1)
                continue
            
            # Try to fetch HTML page first
            html = self._fetch_category_page(category)
            if html:
                report = self._parse_html_page(html, category, vuln_type, cwe, severity)
                if report:
                    self._save_report(report)
                    reports.append(report)
                    if progress and task:
                        progress.update(task, advance=1)
                    continue
            
            # Fall back to raw README
            readme = self._fetch_raw_readme(category)
            if readme:
                report = self._parse_markdown_content(readme, category, vuln_type, cwe, severity)
                if report:
                    self._save_report(report)
                    reports.append(report)
                    if progress and task:
                        progress.update(task, advance=1)
        
        console.print(f"[green]Scraped {len(reports)} new PayloadsAllTheThings entries[/green]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with PayloadsScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=5)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title[:60]}... ({r.vuln_type})")
