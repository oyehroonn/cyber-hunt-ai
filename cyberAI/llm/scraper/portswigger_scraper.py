"""
PortSwigger Web Security Academy Scraper

Scrapes vulnerability labs and write-ups from PortSwigger's Web Security Academy.
"""

import re
from typing import Optional
from pathlib import Path

from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class PortSwiggerScraper(BaseScraper):
    """Scraper for PortSwigger Web Security Academy labs and write-ups."""
    
    SOURCE_NAME = "portswigger"
    BASE_URL = "https://portswigger.net"
    ALL_LABS_URL = "https://portswigger.net/web-security/all-labs"
    ALL_MATERIALS_URL = "https://portswigger.net/web-security/all-materials"
    REQUEST_DELAY = 1.0
    
    VULN_CLASS_MAP = {
        "sql-injection": "SQL Injection",
        "authentication": "Authentication Bypass",
        "path-traversal": "Path Traversal",
        "file-path-traversal": "Path Traversal",
        "command-injection": "Command Injection",
        "os-command-injection": "Command Injection",
        "business-logic": "Business Logic",
        "logic-flaws": "Business Logic",
        "information-disclosure": "Information Disclosure",
        "access-control": "Broken Access Control",
        "file-upload": "Unrestricted File Upload",
        "race-conditions": "Race Condition",
        "ssrf": "SSRF",
        "xxe": "XXE",
        "xss": "XSS",
        "cross-site-scripting": "XSS",
        "csrf": "CSRF",
        "cors": "CORS Misconfiguration",
        "clickjacking": "Clickjacking",
        "dom-based": "DOM-based Vulnerabilities",
        "websockets": "WebSocket Vulnerabilities",
        "insecure-deserialization": "Insecure Deserialization",
        "graphql": "GraphQL Vulnerabilities",
        "api-testing": "API Testing",
        "jwt": "JWT Vulnerabilities",
        "oauth": "OAuth Vulnerabilities",
        "prototype-pollution": "Prototype Pollution",
        "essential-skills": "Essential Skills",
        "host-header": "Host Header Injection",
        "http-request-smuggling": "HTTP Request Smuggling",
        "request-smuggling": "HTTP Request Smuggling",
        "web-cache-poisoning": "Web Cache Poisoning",
        "web-cache-deception": "Web Cache Deception",
        "web-llm-attacks": "LLM Attacks",
        "nosql-injection": "NoSQL Injection",
        "server-side-template-injection": "Template Injection",
    }
    
    SEVERITY_MAP = {
        "apprentice": "low",
        "practitioner": "medium",
        "expert": "high",
    }
    
    CWE_MAP = {
        "SQL Injection": "CWE-89",
        "XSS": "CWE-79",
        "CSRF": "CWE-352",
        "SSRF": "CWE-918",
        "XXE": "CWE-611",
        "Path Traversal": "CWE-22",
        "Command Injection": "CWE-78",
        "Authentication Bypass": "CWE-287",
        "Broken Access Control": "CWE-284",
        "Information Disclosure": "CWE-200",
        "Insecure Deserialization": "CWE-502",
        "Race Condition": "CWE-362",
        "Business Logic": "CWE-840",
        "CORS Misconfiguration": "CWE-942",
        "Clickjacking": "CWE-1021",
        "Open Redirect": "CWE-601",
        "JWT Vulnerabilities": "CWE-347",
        "NoSQL Injection": "CWE-943",
    }
    
    def _fetch_all_labs(self) -> list[dict]:
        """Fetch list of all labs from the all-labs page."""
        response = self._fetch_with_retry(self.ALL_LABS_URL)
        if not response or response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        labs = []
        
        # Find all lab entries
        lab_links = soup.find_all("a", href=re.compile(r"/web-security/.*?/lab-"))
        
        for link in lab_links:
            try:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                
                # Extract difficulty/level
                parent = link.find_parent("div") or link.find_parent("li")
                difficulty = "practitioner"
                if parent:
                    diff_elem = parent.find(class_=re.compile(r"level|difficulty", re.I))
                    if diff_elem:
                        diff_text = diff_elem.get_text(strip=True).lower()
                        for key in self.SEVERITY_MAP:
                            if key in diff_text:
                                difficulty = key
                                break
                    else:
                        parent_text = parent.get_text().lower()
                        for key in self.SEVERITY_MAP:
                            if key in parent_text:
                                difficulty = key
                                break
                
                # Extract vulnerability class from URL
                vuln_class = None
                for key, value in self.VULN_CLASS_MAP.items():
                    if key in href:
                        vuln_class = value
                        break
                
                # Generate lab ID from URL
                lab_id = self._generate_id(href)
                
                labs.append({
                    "id": lab_id,
                    "title": title,
                    "url": f"{self.BASE_URL}{href}" if href.startswith("/") else href,
                    "difficulty": difficulty,
                    "vuln_class": vuln_class,
                })
                
            except Exception as e:
                continue
        
        return labs
    
    def _fetch_materials(self) -> list[dict]:
        """Fetch learning materials (theory pages) from all-materials page."""
        response = self._fetch_with_retry(self.ALL_MATERIALS_URL)
        if not response or response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        materials = []
        seen_hrefs = set()
        
        # Find all material links (topic pages, sub-pages)
        links = soup.find_all("a", href=re.compile(r"/web-security/"))
        
        for link in links:
            try:
                href = link.get("href", "")
                # Normalize: strip fragment and query
                path = href.split("?")[0].split("#")[0].strip("/") or href
                if path in seen_hrefs:
                    continue
                title = link.get_text(strip=True)
                
                # Skip lab links (already handled), dashboard, empty titles
                if "/lab-" in href or "dashboard" in href or not title or len(title) < 2:
                    continue
                # Skip "all materials", "all labs" type links
                if re.search(r"all-(labs|materials|topics)", href):
                    continue
                seen_hrefs.add(path)
                
                vuln_class = None
                for key, value in self.VULN_CLASS_MAP.items():
                    if key in href:
                        vuln_class = value
                        break
                
                material_id = self._generate_id(href)
                
                materials.append({
                    "id": material_id,
                    "title": title,
                    "url": f"{self.BASE_URL}{href}" if href.startswith("/") else href,
                    "vuln_class": vuln_class,
                })
                
            except Exception:
                continue
        
        return materials
    
    def _scrape_all_materials(self, max_reports: int) -> list[RawReport]:
        """Fetch all learning materials from all-materials and save as reports."""
        reports = []
        materials = self._fetch_materials()
        console.print(f"[dim]Found {len(materials)} material pages[/dim]")
        for mat in materials:
            if len(reports) >= max_reports:
                break
            if self._report_exists(mat["id"]):
                continue
            content = self._fetch_page_content(mat["url"])
            if not content or not content.get("body") or len(content.get("body", "")) < 100:
                continue
            report = RawReport(
                id=mat["id"],
                source=self.SOURCE_NAME,
                title=mat["title"],
                url=mat["url"],
                vuln_type=mat.get("vuln_class"),
                cwe=self.CWE_MAP.get(mat.get("vuln_class")) if mat.get("vuln_class") else None,
                severity="high",
                body=content.get("body"),
                description=content.get("description"),
                metadata={
                    "type": "material",
                    "solution": content.get("solution"),
                    "attack_vector": content.get("attack_vector"),
                    "remediation": content.get("remediation"),
                },
            )
            self._save_report(report)
            reports.append(report)
        return reports
    
    def _fetch_page_content(self, url: str) -> Optional[dict]:
        """Fetch full content from a lab or material page."""
        response = self._fetch_with_retry(url)
        if not response or response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        content = {}
        
        try:
            # Find main content area
            main = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
            
            if main:
                # Get full text
                content["body"] = main.get_text(separator="\n", strip=True)
                
                # Extract specific sections
                sections = main.find_all(["h2", "h3"])
                for section in sections:
                    section_title = section.get_text(strip=True).lower()
                    next_elem = section.find_next_sibling()
                    
                    if next_elem:
                        section_text = next_elem.get_text(separator="\n", strip=True)
                        
                        if "solution" in section_title:
                            content["solution"] = section_text
                        elif "description" in section_title:
                            content["description"] = section_text
                        elif "how to" in section_title or "exploit" in section_title:
                            content["attack_vector"] = section_text
                        elif "prevent" in section_title or "remediation" in section_title:
                            content["remediation"] = section_text
            
        except Exception as e:
            console.print(f"[dim]Error parsing page: {e}[/dim]")
        
        return content
    
    def _fetch_vuln_category_pages(self) -> list[RawReport]:
        """Fetch main vulnerability category pages for comprehensive coverage."""
        reports = []
        
        # Updated category paths with correct PortSwigger URLs
        categories = [
            "/web-security/sql-injection",
            "/web-security/authentication",
            "/web-security/access-control",
            "/web-security/ssrf",
            "/web-security/xxe",
            "/web-security/cross-site-scripting",  # Fixed: was /xss
            "/web-security/csrf",
            "/web-security/cors",
            "/web-security/file-upload",
            "/web-security/os-command-injection",
            "/web-security/logic-flaws",  # Fixed: was /business-logic-vulnerabilities
            "/web-security/information-disclosure",
            "/web-security/race-conditions",
            "/web-security/jwt",
            "/web-security/oauth",
            "/web-security/graphql",
            "/web-security/api-testing",
            "/web-security/nosql-injection",
            "/web-security/prototype-pollution",
            "/web-security/request-smuggling",
            "/web-security/web-cache-poisoning",
            "/web-security/clickjacking",
            "/web-security/dom-based",
            "/web-security/websockets",
            "/web-security/insecure-deserialization",
            "/web-security/server-side-template-injection",
            "/web-security/path-traversal",
            "/web-security/file-path-traversal",
        ]
        
        for category_path in categories:
            url = f"{self.BASE_URL}{category_path}"
            cat_id = self._generate_id(category_path)
            
            if self._report_exists(cat_id):
                continue
            
            content = self._fetch_page_content(url)
            if not content or not content.get("body"):
                continue
            
            # Determine vuln class
            vuln_class = None
            for key, value in self.VULN_CLASS_MAP.items():
                if key in category_path:
                    vuln_class = value
                    break
            
            report = RawReport(
                id=cat_id,
                source=self.SOURCE_NAME,
                title=f"PortSwigger: {vuln_class or category_path.split('/')[-1]}",
                url=url,
                vuln_type=vuln_class,
                cwe=self.CWE_MAP.get(vuln_class),
                severity="high",  # Category pages are comprehensive
                body=content.get("body"),
                description=content.get("description"),
                metadata={
                    "type": "category_overview",
                    "solution": content.get("solution"),
                    "attack_vector": content.get("attack_vector"),
                    "remediation": content.get("remediation"),
                }
            )
            
            self._save_report(report)
            reports.append(report)
        
        return reports
    
    def scrape(self, max_reports: int = 50, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape PortSwigger Web Security Academy.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        
        console.print(f"[cyan]Scraping PortSwigger Web Security Academy (target: {max_reports} entries)...[/cyan]")
        
        # First get category overview pages
        category_reports = self._fetch_vuln_category_pages()
        reports.extend(category_reports)
        
        if progress and task:
            progress.update(task, advance=len(category_reports))
        
        if len(reports) >= max_reports:
            console.print(f"[green]Scraped {len(reports)} new PortSwigger entries[/green]")
            return reports[:max_reports]
        
        # All learning materials (theory pages from all-materials)
        remaining = max_reports - len(reports)
        material_reports = self._scrape_all_materials(remaining)
        reports.extend(material_reports)
        if progress and task:
            progress.update(task, advance=len(material_reports))
        if len(reports) >= max_reports:
            console.print(f"[green]Scraped {len(reports)} new PortSwigger entries[/green]")
            return reports[:max_reports]
        
        # Fetch all labs
        labs = self._fetch_all_labs()
        console.print(f"[dim]Found {len(labs)} labs[/dim]")
        
        for lab in labs:
            if len(reports) >= max_reports:
                break
            
            if self._report_exists(lab["id"]):
                continue
            
            # Fetch lab content
            content = self._fetch_page_content(lab["url"])
            
            vuln_class = lab.get("vuln_class")
            
            report = RawReport(
                id=lab["id"],
                source=self.SOURCE_NAME,
                title=lab["title"],
                url=lab["url"],
                vuln_type=vuln_class,
                cwe=self.CWE_MAP.get(vuln_class) if vuln_class else None,
                severity=self.SEVERITY_MAP.get(lab.get("difficulty", "practitioner"), "medium"),
                body=content.get("body") if content else None,
                description=content.get("description") if content else None,
                metadata={
                    "type": "lab",
                    "difficulty": lab.get("difficulty"),
                    "solution": content.get("solution") if content else None,
                    "attack_vector": content.get("attack_vector") if content else None,
                }
            )
            
            self._save_report(report)
            reports.append(report)
            
            if progress and task:
                progress.update(task, advance=1)
        
        console.print(f"[green]Scraped {len(reports)} new PortSwigger entries[/green]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with PortSwiggerScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=10)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:5]:
            print(f"  - {r.title} ({r.vuln_type})")
