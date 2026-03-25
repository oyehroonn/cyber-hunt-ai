"""
General Security Write-up Scraper

Configurable scraper for security blogs, HackTricks, OWASP, and other resources.
"""

import re
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()

# Page with sidebar listing all OWASP cheat sheets (for discovery)
OWASP_CHEATSHEETS_INDEX_URL = "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html"

DEFAULT_SOURCES = [
    # OWASP Cheat Sheets: discover all from sidebar (ul.md-nav__list), then scrape each
    {
        "name": "owasp_cheatsheets",
        "url": OWASP_CHEATSHEETS_INDEX_URL,
        "type": "owasp_discover",
    },
    # OWASP Top 10 2021
    {
        "name": "owasp_top10_2021",
        "url": "https://owasp.org/Top10/",
        "type": "page_with_links",
        "link_pattern": r"/Top10/A",
    },
    
    # OWASP Cheat Sheets - Comprehensive list
    {
        "name": "owasp_csrf",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_auth",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_session",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_sql_injection",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_xss",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_access_control",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_input_validation",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_api_security",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_jwt",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_file_upload",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_ssrf",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_xxe",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_deserialization",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_clickjacking",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_content_security_policy",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_dom_xss",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_error_handling",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_graphql",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_injection_prevention",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_ldap_injection",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/LDAP_Injection_Prevention_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_mass_assignment",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_oauth",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/OAuth_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_os_command_injection",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_password_storage",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_query_parameterization",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_race_conditions",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Race_Conditions_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_secrets_management",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_unvalidated_redirects",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_vulnerable_dependency",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Vulnerable_Dependency_Management_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_web_service_security",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Web_Service_Security_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_nodejs_security",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_docker_security",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html",
        "type": "single_page",
    },
    {
        "name": "owasp_kubernetes_security",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html",
        "type": "single_page",
    },
    
    # HackTricks sections
    {
        "name": "hacktricks_web",
        "url": "https://book.hacktricks.xyz/pentesting-web/web-vulnerabilities-methodology",
        "type": "single_page",
    },
    {
        "name": "hacktricks_techniques",
        "url": "https://book.hacktricks.xyz/generic-methodologies-and-resources/external-recon-methodology",
        "type": "single_page",
    },
    {
        "name": "hacktricks_sqli",
        "url": "https://book.hacktricks.xyz/pentesting-web/sql-injection",
        "type": "single_page",
    },
    {
        "name": "hacktricks_xss",
        "url": "https://book.hacktricks.xyz/pentesting-web/xss-cross-site-scripting",
        "type": "single_page",
    },
    {
        "name": "hacktricks_ssrf",
        "url": "https://book.hacktricks.xyz/pentesting-web/ssrf-server-side-request-forgery",
        "type": "single_page",
    },
    {
        "name": "hacktricks_idor",
        "url": "https://book.hacktricks.xyz/pentesting-web/idor",
        "type": "single_page",
    },
    {
        "name": "hacktricks_race",
        "url": "https://book.hacktricks.xyz/pentesting-web/race-condition",
        "type": "single_page",
    },
    {
        "name": "hacktricks_oauth",
        "url": "https://book.hacktricks.xyz/pentesting-web/oauth-to-account-takeover",
        "type": "single_page",
    },
    {
        "name": "hacktricks_jwt",
        "url": "https://book.hacktricks.xyz/pentesting-web/hacking-jwt-json-web-tokens",
        "type": "single_page",
    },
    {
        "name": "hacktricks_cors",
        "url": "https://book.hacktricks.xyz/pentesting-web/cors-bypass",
        "type": "single_page",
    },
]


class GeneralScraper(BaseScraper):
    """Configurable scraper for general security resources."""
    
    SOURCE_NAME = "general"
    REQUEST_DELAY = 1.5
    
    VULN_PATTERNS = [
        (r"sql.?inject", "SQL Injection", "CWE-89"),
        (r"xss|cross.?site.?script", "XSS", "CWE-79"),
        (r"csrf|cross.?site.?request", "CSRF", "CWE-352"),
        (r"ssrf|server.?side.?request", "SSRF", "CWE-918"),
        (r"xxe|xml.?external", "XXE", "CWE-611"),
        (r"idor|insecure.?direct.?object", "IDOR", "CWE-639"),
        (r"auth.?bypass|broken.?auth", "Authentication Bypass", "CWE-287"),
        (r"access.?control|authorization", "Broken Access Control", "CWE-284"),
        (r"path.?traversal|directory.?traversal|lfi|local.?file", "Path Traversal", "CWE-22"),
        (r"command.?inject|os.?command|rce", "Command Injection", "CWE-78"),
        (r"deserializ", "Insecure Deserialization", "CWE-502"),
        (r"file.?upload", "Unrestricted File Upload", "CWE-434"),
        (r"open.?redirect", "Open Redirect", "CWE-601"),
        (r"session.?fixation|session.?hijack", "Session Vulnerabilities", "CWE-384"),
        (r"jwt|json.?web.?token", "JWT Vulnerabilities", "CWE-347"),
        (r"race.?condition", "Race Condition", "CWE-362"),
        (r"privilege.?escalat", "Privilege Escalation", "CWE-269"),
        (r"business.?logic", "Business Logic", "CWE-840"),
        (r"cors", "CORS Misconfiguration", "CWE-942"),
        (r"clickjack", "Clickjacking", "CWE-1021"),
        (r"api.?security|rest.?security|graphql", "API Security", None),
        (r"oauth", "OAuth Vulnerabilities", "CWE-287"),
        (r"websocket", "WebSocket Vulnerabilities", None),
        (r"cache.?poison", "Web Cache Poisoning", None),
        (r"request.?smuggl", "HTTP Request Smuggling", "CWE-444"),
        (r"prototype.?pollut", "Prototype Pollution", "CWE-1321"),
    ]
    
    def __init__(self, data_dir: Path, sources: Optional[list[dict]] = None):
        super().__init__(data_dir)
        self.sources = sources or DEFAULT_SOURCES
    
    def _extract_page_content(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract clean content from a page."""
        content = {
            "title": "",
            "body": "",
            "vuln_type": None,
            "cwe": None,
        }
        
        # Remove navigation, footer, scripts, styles
        for element in soup.find_all(["nav", "footer", "script", "style", "aside"]):
            element.decompose()
        
        # Extract title
        title = soup.find("h1") or soup.find("title")
        if title:
            content["title"] = title.get_text(strip=True)
        
        # Extract main content
        main = (
            soup.find("main") or 
            soup.find("article") or 
            soup.find("div", class_=re.compile(r"content|markdown|article", re.I)) or
            soup.find("div", id=re.compile(r"content|main", re.I)) or
            soup.body
        )
        
        if main:
            content["body"] = main.get_text(separator="\n", strip=True)
        
        # Detect vulnerability type from title and URL
        text_to_check = (content["title"] + " " + url).lower()
        for pattern, vuln_type, cwe in self.VULN_PATTERNS:
            if re.search(pattern, text_to_check):
                content["vuln_type"] = vuln_type
                content["cwe"] = cwe
                break
        
        return content
    
    def _scrape_single_page(self, source: dict) -> Optional[RawReport]:
        """Scrape a single page source."""
        url = source["url"]
        report_id = self._generate_id(url)
        
        if self._report_exists(report_id):
            return None
        
        response = self._fetch_with_retry(url)
        if not response or response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        content = self._extract_page_content(soup, url)
        
        if not content["body"] or len(content["body"]) < 100:
            return None
        
        report = RawReport(
            id=report_id,
            source=self.SOURCE_NAME,
            title=content["title"] or source["name"],
            url=url,
            body=content["body"],
            vuln_type=content["vuln_type"],
            cwe=content["cwe"],
            severity="medium",
            metadata={
                "source_name": source["name"],
                "source_type": source["type"],
            }
        )
        
        return report
    
    def _scrape_page_with_links(self, source: dict, max_links: int = 10) -> list[RawReport]:
        """Scrape a page and follow links matching pattern."""
        reports = []
        url = source["url"]
        link_pattern = source.get("link_pattern", "")
        
        response = self._fetch_with_retry(url)
        if not response or response.status_code != 200:
            return reports
        
        soup = BeautifulSoup(response.text, "html.parser")
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        # First, scrape the main page itself
        main_report = self._scrape_single_page(source)
        if main_report:
            self._save_report(main_report)
            reports.append(main_report)
        
        # Find and follow links
        links = soup.find_all("a", href=re.compile(link_pattern) if link_pattern else True)
        seen_urls = set()
        
        for link in links[:max_links]:
            href = link.get("href", "")
            if not href or href.startswith("#"):
                continue
            
            # Build full URL
            if href.startswith("/"):
                full_url = base_url + href
            elif href.startswith("http"):
                full_url = href
            else:
                full_url = urljoin(url, href)
            
            # Skip if already seen or is the main page
            if full_url in seen_urls or full_url == url:
                continue
            seen_urls.add(full_url)
            
            # Create a sub-source and scrape
            sub_source = {
                "name": f"{source['name']}_{self._generate_id(full_url)[:6]}",
                "url": full_url,
                "type": "single_page",
            }
            
            report = self._scrape_single_page(sub_source)
            if report:
                self._save_report(report)
                reports.append(report)
        
        return reports
    
    def _discover_owasp_cheatsheet_urls(self, index_url: str) -> list[str]:
        """Discover all OWASP cheat sheet URLs from sidebar nav (ul.md-nav__list)."""
        urls = []
        try:
            response = self._fetch_with_retry(index_url)
            if not response or response.status_code != 200:
                return urls
            soup = BeautifulSoup(response.text, "html.parser")
            base = f"{urlparse(index_url).scheme}://{urlparse(index_url).netloc}"
            nav = soup.find("ul", class_="md-nav__list")
            if not nav:
                nav = soup.find("nav", class_=re.compile(r"md-nav"))
                if nav:
                    nav = nav.find("ul", class_=re.compile(r"md-nav__list"))
            if not nav:
                # Fallback: any link to a Cheat_Sheet page
                for a in soup.find_all("a", href=re.compile(r".*Cheat_Sheet.*\.html")):
                    href = a.get("href", "")
                    if href and "Cheat_Sheet" in href:
                        full = urljoin(base + "/", href)
                        if full not in urls:
                            urls.append(full)
                return urls
            for a in nav.find_all("a", href=True):
                href = a.get("href", "")
                if "Cheat_Sheet" in href or "cheatsheet" in href.lower():
                    full = urljoin(base + "/", href)
                    if full not in urls:
                        urls.append(full)
        except Exception as e:
            console.print(f"[dim]OWASP discover error: {e}[/dim]")
        return urls
    
    def _scrape_owasp_discover(self, source: dict, max_reports: int) -> list[RawReport]:
        """Discover OWASP cheat sheets from sidebar and scrape each."""
        reports = []
        urls = self._discover_owasp_cheatsheet_urls(source["url"])
        console.print(f"[dim]Discovered {len(urls)} OWASP cheat sheets[/dim]")
        for url in urls:
            if len(reports) >= max_reports:
                break
            sub = {"name": f"owasp_{self._generate_id(url)[:8]}", "url": url, "type": "single_page"}
            report = self._scrape_single_page(sub)
            if report:
                self._save_report(report)
                reports.append(report)
        return reports
    
    def add_source(self, name: str, url: str, source_type: str = "single_page",
                   link_pattern: Optional[str] = None):
        """Add a new source to scrape."""
        source = {
            "name": name,
            "url": url,
            "type": source_type,
        }
        if link_pattern:
            source["link_pattern"] = link_pattern
        self.sources.append(source)
    
    def scrape(self, max_reports: int = 50, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape all configured sources.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        
        console.print(f"[cyan]Scraping general security resources (target: {max_reports} entries)...[/cyan]")
        console.print(f"[dim]Configured sources: {len(self.sources)}[/dim]")
        
        for source in self.sources:
            if len(reports) >= max_reports:
                break
            
            try:
                if source["type"] == "single_page":
                    report = self._scrape_single_page(source)
                    if report:
                        self._save_report(report)
                        reports.append(report)
                        
                        if progress and task:
                            progress.update(task, advance=1)
                
                elif source["type"] == "page_with_links":
                    remaining = max_reports - len(reports)
                    source_reports = self._scrape_page_with_links(source, max_links=min(10, remaining))
                    reports.extend(source_reports)
                    
                    if progress and task:
                        progress.update(task, advance=len(source_reports))
                
                elif source["type"] == "owasp_discover":
                    remaining = max_reports - len(reports)
                    source_reports = self._scrape_owasp_discover(source, max_reports=remaining)
                    reports.extend(source_reports)
                    if progress and task:
                        progress.update(task, advance=len(source_reports))
                
            except Exception as e:
                console.print(f"[dim]Error scraping {source['name']}: {e}[/dim]")
                continue
        
        console.print(f"[green]Scraped {len(reports)} new general security entries[/green]")
        return reports
    
    def scrape_hacktricks(self, max_pages: int = 20) -> list[RawReport]:
        """Specifically scrape HackTricks web security sections."""
        hacktricks_sections = [
            "https://book.hacktricks.xyz/pentesting-web/sql-injection",
            "https://book.hacktricks.xyz/pentesting-web/xss-cross-site-scripting",
            "https://book.hacktricks.xyz/pentesting-web/csrf-cross-site-request-forgery",
            "https://book.hacktricks.xyz/pentesting-web/ssrf-server-side-request-forgery",
            "https://book.hacktricks.xyz/pentesting-web/xxe-xee-xml-external-entity",
            "https://book.hacktricks.xyz/pentesting-web/idor",
            "https://book.hacktricks.xyz/pentesting-web/deserialization",
            "https://book.hacktricks.xyz/pentesting-web/file-upload",
            "https://book.hacktricks.xyz/pentesting-web/race-condition",
            "https://book.hacktricks.xyz/pentesting-web/oauth-to-account-takeover",
            "https://book.hacktricks.xyz/pentesting-web/jwt-json-web-tokens",
            "https://book.hacktricks.xyz/pentesting-web/cors-bypass",
            "https://book.hacktricks.xyz/pentesting-web/clickjacking",
            "https://book.hacktricks.xyz/pentesting-web/http-request-smuggling",
            "https://book.hacktricks.xyz/pentesting-web/cache-poisoning",
        ]
        
        reports = []
        for url in hacktricks_sections[:max_pages]:
            source = {
                "name": f"hacktricks_{urlparse(url).path.split('/')[-1]}",
                "url": url,
                "type": "single_page",
            }
            report = self._scrape_single_page(source)
            if report:
                self._save_report(report)
                reports.append(report)
        
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with GeneralScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=5)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title[:60]}... ({r.vuln_type})")
