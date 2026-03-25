"""
CWE Database Scraper

Scrapes Common Weakness Enumeration (CWE) entries from MITRE.
"""

import re
from typing import Optional
from pathlib import Path

from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class CWEScraper(BaseScraper):
    """Scraper for CWE entries from MITRE."""
    
    SOURCE_NAME = "cwe"
    BASE_URL = "https://cwe.mitre.org"
    REQUEST_DELAY = 1.0
    
    # Web-related CWEs with their categories
    WEB_CWES = [
        # Injection
        ("79", "XSS", "high"),
        ("89", "SQL Injection", "critical"),
        ("78", "Command Injection", "critical"),
        ("77", "Command Injection", "critical"),
        ("94", "Code Injection", "critical"),
        ("917", "Expression Language Injection", "high"),
        ("943", "NoSQL Injection", "high"),
        
        # Authentication/Authorization
        ("287", "Authentication Bypass", "critical"),
        ("284", "Broken Access Control", "high"),
        ("285", "Improper Authorization", "high"),
        ("306", "Missing Authentication", "critical"),
        ("862", "Missing Authorization", "high"),
        ("863", "Incorrect Authorization", "high"),
        ("639", "IDOR", "high"),
        ("352", "CSRF", "high"),
        
        # Data Exposure
        ("200", "Information Disclosure", "medium"),
        ("209", "Error Information Leak", "low"),
        ("532", "Log File Information Leak", "medium"),
        ("598", "URL Query String Exposure", "medium"),
        
        # Input Validation
        ("20", "Improper Input Validation", "high"),
        ("22", "Path Traversal", "high"),
        ("23", "Relative Path Traversal", "high"),
        ("36", "Absolute Path Traversal", "high"),
        ("434", "Unrestricted File Upload", "critical"),
        ("601", "Open Redirect", "medium"),
        
        # Session Management
        ("384", "Session Fixation", "high"),
        ("613", "Session Expiration Issues", "medium"),
        ("614", "HTTPS Session Cookie", "medium"),
        
        # Cryptographic Issues
        ("327", "Broken Cryptography", "high"),
        ("328", "Weak Hash", "medium"),
        ("347", "JWT Verification Failure", "high"),
        ("757", "Insecure Algorithm Selection", "high"),
        
        # Configuration
        ("16", "Configuration Issues", "medium"),
        ("942", "CORS Misconfiguration", "medium"),
        ("1021", "Clickjacking", "medium"),
        ("444", "HTTP Request Smuggling", "high"),
        
        # Serialization
        ("502", "Insecure Deserialization", "critical"),
        ("915", "Improper Controlled Modification", "high"),
        
        # Race Conditions
        ("362", "Race Condition", "high"),
        ("367", "TOCTOU Race Condition", "high"),
        
        # XML
        ("611", "XXE", "high"),
        ("91", "XML Injection", "high"),
        
        # Server-Side
        ("918", "SSRF", "high"),
        ("840", "Business Logic Errors", "high"),
        
        # Client-Side
        ("1321", "Prototype Pollution", "high"),
        ("829", "Untrusted Functionality Inclusion", "high"),
        
        # API
        ("285", "Improper API Authorization", "high"),
    ]
    
    def _fetch_cwe_page(self, cwe_id: str) -> Optional[str]:
        """Fetch a CWE detail page."""
        url = f"{self.BASE_URL}/data/definitions/{cwe_id}.html"
        response = self._fetch_with_retry(url)
        if response and response.status_code == 200:
            return response.text
        return None
    
    def _parse_cwe_page(self, cwe_id: str, html: str, vuln_type: str, severity: str) -> Optional[RawReport]:
        """Parse a CWE page into a RawReport."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract title
            title_elem = soup.find("h2")
            title = title_elem.get_text(strip=True) if title_elem else f"CWE-{cwe_id}"
            
            # Clean up title
            title = re.sub(r"^CWE-\d+:\s*", "", title)
            title = f"CWE-{cwe_id}: {title}"
            
            # Extract description
            description = ""
            desc_div = soup.find("div", {"id": "Description"})
            if desc_div:
                desc_content = desc_div.find_next("div", class_="indent")
                if desc_content:
                    description = desc_content.get_text(separator=" ", strip=True)
            
            # Extract extended description
            extended = ""
            ext_div = soup.find("div", {"id": "Extended_Description"})
            if ext_div:
                ext_content = ext_div.find_next("div", class_="indent")
                if ext_content:
                    extended = ext_content.get_text(separator=" ", strip=True)
            
            # Extract common consequences
            consequences = ""
            cons_div = soup.find("div", {"id": "Common_Consequences"})
            if cons_div:
                cons_table = cons_div.find_next("table")
                if cons_table:
                    consequences = cons_table.get_text(separator=" ", strip=True)
            
            # Extract potential mitigations
            mitigations = ""
            mit_div = soup.find("div", {"id": "Potential_Mitigations"})
            if mit_div:
                mit_content = mit_div.find_next("div", class_="indent")
                if mit_content:
                    mitigations = mit_content.get_text(separator="\n", strip=True)
            
            # Extract detection methods
            detection = ""
            det_div = soup.find("div", {"id": "Detection_Methods"})
            if det_div:
                det_content = det_div.find_next("div", class_="indent")
                if det_content:
                    detection = det_content.get_text(separator="\n", strip=True)
            
            # Extract examples
            examples = ""
            ex_div = soup.find("div", {"id": "Demonstrative_Examples"})
            if ex_div:
                ex_content = ex_div.find_next("div", class_="indent")
                if ex_content:
                    examples = ex_content.get_text(separator="\n", strip=True)[:2000]
            
            # Build body
            body_parts = []
            if description:
                body_parts.append(f"Description:\n{description}")
            if extended:
                body_parts.append(f"\nExtended Description:\n{extended}")
            if consequences:
                body_parts.append(f"\nConsequences:\n{consequences}")
            if mitigations:
                body_parts.append(f"\nMitigations:\n{mitigations}")
            if detection:
                body_parts.append(f"\nDetection Methods:\n{detection}")
            if examples:
                body_parts.append(f"\nExamples:\n{examples}")
            
            body = "\n".join(body_parts)
            
            if not body or len(body) < 100:
                return None
            
            report = RawReport(
                id=f"CWE-{cwe_id}",
                source=self.SOURCE_NAME,
                title=title,
                url=f"{self.BASE_URL}/data/definitions/{cwe_id}.html",
                severity=severity,
                vuln_type=vuln_type,
                cwe=f"CWE-{cwe_id}",
                description=description or extended,
                body=body,
                metadata={
                    "cwe_id": f"CWE-{cwe_id}",
                    "mitigations": mitigations[:1000] if mitigations else None,
                    "detection": detection[:500] if detection else None,
                    "consequences": consequences[:500] if consequences else None,
                }
            )
            
            return report
            
        except Exception as e:
            console.print(f"[dim]Error parsing CWE-{cwe_id}: {e}[/dim]")
            return None
    
    def scrape(self, max_reports: int = 50, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape CWE entries from MITRE.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        
        console.print(f"[cyan]Scraping CWE database (target: {max_reports} entries)...[/cyan]")
        
        for cwe_id, vuln_type, severity in self.WEB_CWES:
            if len(reports) >= max_reports:
                break
            
            report_id = f"CWE-{cwe_id}"
            
            # Skip if already exists
            if self._report_exists(report_id):
                if progress and task:
                    progress.update(task, advance=1)
                continue
            
            html = self._fetch_cwe_page(cwe_id)
            if not html:
                continue
            
            report = self._parse_cwe_page(cwe_id, html, vuln_type, severity)
            if report:
                self._save_report(report)
                reports.append(report)
                
                if progress and task:
                    progress.update(task, advance=1)
        
        console.print(f"[green]Scraped {len(reports)} new CWE entries[/green]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with CWEScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=5)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title} ({r.severity})")
