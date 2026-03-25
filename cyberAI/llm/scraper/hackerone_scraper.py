"""
HackerOne Report Scraper

Scrapes publicly disclosed vulnerability reports from HackerOne's hacktivity feed.
Supports optional login via HACKERONE_EMAIL and HACKERONE_PASSWORD in .env for more reports.
"""

import os
import re
import json
from typing import Optional
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class HackerOneScraper(BaseScraper):
    """Scraper for HackerOne disclosed vulnerability reports."""
    
    SOURCE_NAME = "hackerone"
    HACKTIVITY_API = "https://hackerone.com/graphql"
    SIGN_IN_URL = "https://hackerone.com/users/sign_in"
    HACKTIVITY_OVERVIEW_URL = "https://hackerone.com/hacktivity/overview"
    REQUEST_DELAY = 1.5  # Slightly longer delay for HackerOne
    
    SEVERITY_MAP = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "none": "informational",
    }
    
    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self._email = (os.environ.get("HACKERONE_EMAIL") or "").strip()
        self._password = (os.environ.get("HACKERONE_PASSWORD") or "").strip()
        self._logged_in = False
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    def _ensure_authenticated(self) -> bool:
        """Log in with HACKERONE_EMAIL and HACKERONE_PASSWORD if set. Returns True if session is usable."""
        if self._logged_in:
            return True
        if not self._email or not self._password:
            return False
        client = self._get_client()
        try:
            # GET login page for CSRF token
            self._rate_limit()
            r = client.get(
                self.SIGN_IN_URL,
                headers={"User-Agent": self.headers["User-Agent"], "Accept": "text/html"},
            )
            if r.status_code != 200:
                console.print("[dim]HackerOne: could not load login page[/dim]")
                return False
            soup = BeautifulSoup(r.text, "html.parser")
            token_input = soup.find("input", {"name": re.compile(r"authenticity_token|csrf", re.I)})
            if not token_input:
                token_input = soup.find("input", {"type": "hidden"})  # often the first hidden is CSRF
            token = token_input.get("value") if token_input else ""
            if not token:
                console.print("[dim]HackerOne: no CSRF token on login page[/dim]")
                return False
            # POST credentials
            self._rate_limit()
            login_data = {
                "authenticity_token": token,
                "user[email]": self._email,
                "user[password]": self._password,
            }
            r2 = client.post(
                self.SIGN_IN_URL,
                headers={
                    "User-Agent": self.headers["User-Agent"],
                    "Accept": "text/html",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://hackerone.com",
                    "Referer": self.SIGN_IN_URL,
                },
                data=login_data,
            )
            # Success: redirect away from sign_in or session cookie set
            if r2.status_code in (200, 302):
                if "sign_in" not in str(r2.url) or (r2.status_code == 302 and r2.headers.get("location") and "sign_in" not in r2.headers.get("location", "")):
                    self._logged_in = True
                    console.print("[green]HackerOne: logged in successfully[/green]")
                    return True
            console.print("[dim]HackerOne: login failed (check email/password in .env)[/dim]")
        except Exception as e:
            console.print(f"[dim]HackerOne login error: {e}[/dim]")
        return False
    
    def _fetch_hacktivity_page(self, cursor: Optional[str] = None, size: int = 25) -> Optional[dict]:
        """Fetch a page of hacktivity reports using GraphQL API."""
        query = """
        query HacktivityPageQuery($queryString: String, $size: Int, $cursor: String) {
          hacktivity_items(
            query_string: $queryString
            size: $size
            cursor: $cursor
            order_direction: DESC
            order_field: popular
          ) {
            edges {
              node {
                ... on HacktivityItemInterface {
                  id
                  databaseId: _id
                  reporter {
                    username
                  }
                  team {
                    handle
                    name
                  }
                  report {
                    id
                    databaseId: _id
                    title
                    substate
                    url
                    disclosed_at
                    severity_rating
                    cve_ids
                    weakness {
                      name
                      external_id
                    }
                  }
                  severity_rating
                  total_awarded_amount
                  latest_disclosable_activity_at
                }
              }
            }
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
        """
        
        variables = {
            "queryString": "disclosed:true",
            "size": size,
            "cursor": cursor,
        }
        
        try:
            self._rate_limit()
            client = self._get_client()
            response = client.post(
                self.HACKTIVITY_API,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]Error fetching hacktivity: {e}[/red]")
            return None
    
    def _fetch_report_details(self, report_url: str) -> Optional[str]:
        """Fetch full report body from report page."""
        try:
            response = self._fetch_with_retry(report_url)
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to find report body in various possible containers
            body_selectors = [
                "div.report-body",
                "div[data-testid='report-body']",
                "div.spec-vulnerability-information",
                "article",
                "main",
            ]
            
            for selector in body_selectors:
                body = soup.select_one(selector)
                if body:
                    # Clean up the text
                    text = body.get_text(separator="\n", strip=True)
                    if len(text) > 100:
                        return text
            
            # Fallback: get all paragraph text
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
            return text if text else None
            
        except Exception as e:
            console.print(f"[dim]Could not fetch report details: {e}[/dim]")
            return None
    
    def _parse_hacktivity_item(self, item) -> Optional[RawReport]:
        """Parse a hacktivity item into a RawReport."""
        try:
            # Safely handle item being various types
            if not isinstance(item, dict):
                return None
            
            node = item.get("node")
            if not isinstance(node, dict):
                return None
            
            report = node.get("report")
            if not isinstance(report, dict):
                return None
            
            # Get report ID safely
            report_id = report.get("databaseId") or report.get("id")
            if not report_id:
                return None
            report_id = str(report_id)
            
            # Check if already scraped
            if self._report_exists(report_id):
                return None
            
            # Extract title safely
            title = report.get("title")
            if not isinstance(title, str) or not title.strip():
                title = "Unknown HackerOne Report"
            
            # Extract URL safely
            url = report.get("url")
            if not isinstance(url, str) or not url.strip():
                url = f"https://hackerone.com/reports/{report_id}"
            
            # Extract weakness/CWE info safely
            weakness = report.get("weakness")
            cwe = None
            vuln_type = None
            if isinstance(weakness, dict):
                cwe = weakness.get("external_id")
                vuln_type = weakness.get("name")
                if cwe and not isinstance(cwe, str):
                    cwe = str(cwe) if cwe else None
                if vuln_type and not isinstance(vuln_type, str):
                    vuln_type = str(vuln_type) if vuln_type else None
            
            # Severity safely
            severity_raw = node.get("severity_rating")
            severity_str = str(severity_raw).lower() if severity_raw else "none"
            severity = self.SEVERITY_MAP.get(severity_str, "informational")
            
            # Team info safely
            team = node.get("team")
            affected_component = None
            team_handle = None
            if isinstance(team, dict):
                affected_component = team.get("name") or team.get("handle")
                team_handle = team.get("handle")
            
            # Reporter safely
            reporter = node.get("reporter")
            reporter_username = None
            if isinstance(reporter, dict):
                reporter_username = reporter.get("username")
            
            # CVE IDs safely
            cve_ids = report.get("cve_ids")
            if not isinstance(cve_ids, list):
                cve_ids = []
            
            # Build report
            raw_report = RawReport(
                id=report_id,
                source=self.SOURCE_NAME,
                title=title,
                url=url,
                severity=severity,
                vuln_type=vuln_type,
                cwe=cwe,
                affected_component=affected_component,
                disclosed_at=report.get("disclosed_at"),
                bounty=node.get("total_awarded_amount"),
                metadata={
                    "reporter": reporter_username,
                    "team_handle": team_handle,
                    "cve_ids": cve_ids,
                    "substate": report.get("substate"),
                }
            )
            
            return raw_report
            
        except Exception as e:
            console.print(f"[dim]Error parsing hacktivity item: {e}[/dim]")
            return None
    
    def scrape(self, max_reports: int = 60, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape HackerOne disclosed reports.
        
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
        max_pages = (max_reports // 25) + 2
        
        console.print(f"[cyan]Scraping HackerOne hacktivity (target: {max_reports} reports)...[/cyan]")
        if self._email and self._password:
            self._ensure_authenticated()
        else:
            console.print("[dim]No HACKERONE_EMAIL/HACKERONE_PASSWORD in .env; scraping unauthenticated[/dim]")
        
        while len(reports) < max_reports and pages_fetched < max_pages:
            data = self._fetch_hacktivity_page(cursor=cursor, size=25)
            
            if not data or "data" not in data:
                break
            
            hacktivity = data.get("data", {}).get("hacktivity_items", {})
            edges = hacktivity.get("edges", [])
            
            if not edges:
                break
            
            for edge in edges:
                if len(reports) >= max_reports:
                    break
                
                report = self._parse_hacktivity_item(edge)
                if report:
                    # Try to fetch full body (optional, may not always work)
                    # body = self._fetch_report_details(report.url)
                    # if body:
                    #     report.body = body
                    
                    self._save_report(report)
                    reports.append(report)
                    
                    if progress and task:
                        progress.update(task, advance=1)
            
            # Check for next page
            page_info = hacktivity.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            pages_fetched += 1
        
        console.print(f"[green]Scraped {len(reports)} new HackerOne reports[/green]")
        return reports
    
    def scrape_featured_programs(self, max_reports: int = 20) -> list[RawReport]:
        """Scrape reports from featured/popular programs."""
        featured_programs = [
            "security", "nodejs", "rails", "php", "kubernetes",
            "github", "gitlab", "shopify", "uber", "airbnb"
        ]
        
        reports = []
        for program in featured_programs:
            if len(reports) >= max_reports:
                break
            
            query = f"disclosed:true team:{program}"
            # This would need GraphQL query modification
            # For now, skip this method
        
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with HackerOneScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=10)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title} ({r.severity})")
