"""
Bugcrowd Report Scraper

Scrapes publicly disclosed vulnerability reports from Bugcrowd.
"""

import re
from typing import Optional
from pathlib import Path

from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID

from llm.scraper.base_scraper import BaseScraper, RawReport

console = Console()


class BugcrowdScraper(BaseScraper):
    """Scraper for Bugcrowd disclosed vulnerability reports."""
    
    SOURCE_NAME = "bugcrowd"
    BASE_URL = "https://bugcrowd.com"
    DISCLOSURES_URL = "https://bugcrowd.com/disclosures"
    BLOG_BASE_URL = "https://www.bugcrowd.com/blog"
    REQUEST_DELAY = 1.5
    
    # Topic IDs for blog filtering (t__category=<ID>). Security-relevant first.
    BLOG_TOPIC_IDS = [
        (21, "Bug Hunter Methodology"),
        (63, "Vulnerabilities"),
        (27, "Vulnerability Disclosure"),
        (1223, "Hacker Resources"),
        (13, "Researcher Resources"),
        (330, "Report Recap"),
        (1224, "Penetration Testing"),
        (441, "Penetration Testing as a Service"),
        (1225, "Red Teaming"),
        (9, "Attack Surface Management"),
        (29, "Bug Bounty Management"),
        (30, "Success Stories"),
        (587, "Hacker Spotlight"),
        (31, "Researcher Spotlight"),
        (24, "Guest Blogs"),
        (19, "Cybersecurity News"),
        (20, "Thought Leadership"),
    ]
    
    SEVERITY_MAP = {
        "p1": "critical",
        "p2": "high", 
        "p3": "medium",
        "p4": "low",
        "p5": "informational",
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    
    def _fetch_disclosures_page(self, page: int = 1) -> Optional[BeautifulSoup]:
        """Fetch a page of Bugcrowd disclosures."""
        url = f"{self.DISCLOSURES_URL}?page={page}"
        response = self._fetch_with_retry(url)
        
        if not response or response.status_code != 200:
            return None
        
        return BeautifulSoup(response.text, "html.parser")
    
    def _parse_disclosure_card(self, card) -> Optional[dict]:
        """Parse a disclosure card from the listings page."""
        try:
            # Extract disclosure link
            link = card.find("a", href=re.compile(r"/disclosures/"))
            if not link:
                return None
            
            href = link.get("href", "")
            disclosure_id = href.split("/")[-1].split("?")[0]
            
            # Extract title
            title_elem = card.find("h4") or card.find("h3") or link
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Try to extract severity
            severity = "informational"
            severity_elem = card.find(class_=re.compile(r"priority|severity", re.I))
            if severity_elem:
                sev_text = severity_elem.get_text(strip=True).lower()
                for key, val in self.SEVERITY_MAP.items():
                    if key in sev_text:
                        severity = val
                        break
            
            # Extract program name
            program_elem = card.find(class_=re.compile(r"program|company", re.I))
            program = program_elem.get_text(strip=True) if program_elem else None
            
            return {
                "id": disclosure_id,
                "title": title,
                "url": f"{self.BASE_URL}{href}" if href.startswith("/") else href,
                "severity": severity,
                "program": program,
            }
            
        except Exception as e:
            console.print(f"[dim]Error parsing card: {e}[/dim]")
            return None
    
    def _fetch_disclosure_details(self, url: str) -> Optional[dict]:
        """Fetch full disclosure details from the disclosure page."""
        response = self._fetch_with_retry(url)
        if not response or response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        details = {}
        
        try:
            # Extract description/body
            body_selectors = [
                "div.disclosure-body",
                "div.disclosure-content",
                "article",
                "div.markdown-body",
                "main",
            ]
            
            for selector in body_selectors:
                body = soup.select_one(selector)
                if body:
                    details["body"] = body.get_text(separator="\n", strip=True)
                    break
            
            # Extract vulnerability type
            vuln_type_elem = soup.find(text=re.compile(r"vulnerability type|weakness", re.I))
            if vuln_type_elem:
                parent = vuln_type_elem.find_parent()
                if parent:
                    sibling = parent.find_next_sibling()
                    if sibling:
                        details["vuln_type"] = sibling.get_text(strip=True)
            
            # Extract CWE if present
            cwe_match = re.search(r"CWE-(\d+)", response.text)
            if cwe_match:
                details["cwe"] = f"CWE-{cwe_match.group(1)}"
            
            # Extract CVSS if present
            cvss_match = re.search(r"CVSS[:\s]*(\d+\.?\d*)", response.text, re.I)
            if cvss_match:
                details["cvss_score"] = float(cvss_match.group(1))
            
        except Exception as e:
            console.print(f"[dim]Error fetching details: {e}[/dim]")
        
        return details
    
    def _build_blog_listing_url(self, topic_id: Optional[int] = None, page: int = 1) -> str:
        """Build URL for blog listing, optionally filtered by topic and page."""
        if topic_id is not None:
            url = f"{self.BLOG_BASE_URL}/?f__s=&t__category={topic_id}&a__author="
        else:
            url = f"{self.BLOG_BASE_URL}/"
        if page > 1:
            url += "&" if "?" in url else "?"
            url += f"page={page}"
        return url
    
    def _fetch_blog_listing_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a blog listing page and return parsed soup."""
        response = self._fetch_with_retry(url)
        if not response or response.status_code != 200:
            return None
        return BeautifulSoup(response.text, "html.parser")
    
    def _parse_blog_listing(self, soup: BeautifulSoup) -> list[tuple[str, str]]:
        """Extract blog post URLs and titles from a listing page. Returns list of (url, title)."""
        results = []
        seen = set()
        # Links that point to blog posts: /blog/some-slug/ or full URL with /blog/slug
        for a in soup.find_all("a", href=True):
            try:
                href = a.get("href", "").strip()
                if not href or href.startswith("#"):
                    continue
                # Normalize to absolute URL
                if href.startswith("/"):
                    full_url = f"https://www.bugcrowd.com{href}"
                elif "bugcrowd.com/blog/" in href:
                    full_url = href.split("?")[0].rstrip("/") or href
                else:
                    continue
                # Must look like a post: /blog/something (not just /blog or /blog/)
                if "/blog" not in full_url:
                    continue
                path = full_url.replace("https://www.bugcrowd.com", "").replace("http://www.bugcrowd.com", "")
                if path in ("/blog", "/blog/"):
                    continue
                # Has a slug after /blog/ (e.g. /blog/my-post-title/)
                parts = path.strip("/").split("/")
                if len(parts) < 2 or parts[0] != "blog":
                    continue
                slug = parts[1]
                if not slug or len(slug) < 2:
                    continue
                if full_url in seen:
                    continue
                seen.add(full_url)
                title = a.get_text(strip=True) or slug.replace("-", " ").title()
                if len(title) > 200:
                    title = title[:200]
                results.append((full_url, title))
            except Exception:
                continue
        return results
    
    def _scrape_single_blog_post(self, post_url: str, fallback_title: str = "Bugcrowd Blog Post") -> Optional[RawReport]:
        """Fetch a single blog post and return a RawReport, or None on failure."""
        try:
            response = self._fetch_with_retry(post_url)
            if not response or response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            title = fallback_title
            for tag in soup.find_all(["h1"]):
                t = tag.get_text(strip=True)
                if t and len(t) > 2:
                    title = t[:300]
                    break
            body = None
            for selector in ["article", "main", "[class*='post-body']", "[class*='article-body']", "[class*='content']"]:
                node = soup.select_one(selector)
                if node:
                    text = node.get_text(separator="\n", strip=True)
                    if text and len(text) >= 100:
                        body = text[:15000]
                        break
            if not body or len(body) < 100:
                return None
            report_id = self._generate_id(post_url)
            if self._report_exists(report_id):
                return None
            vuln_type = self._detect_vuln_type(title + " " + body)
            report = RawReport(
                id=report_id,
                source=self.SOURCE_NAME,
                title=title,
                url=post_url,
                body=body,
                vuln_type=vuln_type,
                severity="medium",
            )
            return report
        except Exception as e:
            console.print(f"[dim]Error scraping post {post_url[:50]}...: {e}[/dim]")
            return None
    
    def _scrape_blog_writeups(self, max_reports: int = 20) -> list[RawReport]:
        """Scrape blog posts from Bugcrowd blog with topic filtering."""
        reports = []
        seen_urls = set()
        max_pages_per_topic = 3  # Try up to 3 pages per topic
        
        # First try unfiltered blog listing to get recent posts
        for page in range(1, max_pages_per_topic + 1):
            if len(reports) >= max_reports:
                break
            url = self._build_blog_listing_url(topic_id=None, page=page)
            soup = self._fetch_blog_listing_page(url)
            if not soup:
                break
            links = self._parse_blog_listing(soup)
            if not links:
                break
            for post_url, title in links:
                if len(reports) >= max_reports:
                    break
                if post_url in seen_urls:
                    continue
                report_id = self._generate_id(post_url)
                if self._report_exists(report_id):
                    seen_urls.add(post_url)
                    continue
                seen_urls.add(post_url)
                report = self._scrape_single_blog_post(post_url, fallback_title=title)
                if report:
                    self._save_report(report)
                    reports.append(report)
        
        # Then scrape by topic (security-relevant topics)
        for topic_id, topic_name in self.BLOG_TOPIC_IDS:
            if len(reports) >= max_reports:
                break
            for page in range(1, max_pages_per_topic + 1):
                if len(reports) >= max_reports:
                    break
                url = self._build_blog_listing_url(topic_id=topic_id, page=page)
                soup = self._fetch_blog_listing_page(url)
                if not soup:
                    break
                links = self._parse_blog_listing(soup)
                if not links:
                    break
                for post_url, title in links:
                    if len(reports) >= max_reports:
                        break
                    if post_url in seen_urls:
                        continue
                    report_id = self._generate_id(post_url)
                    if self._report_exists(report_id):
                        seen_urls.add(post_url)
                        continue
                    seen_urls.add(post_url)
                    report = self._scrape_single_blog_post(post_url, fallback_title=title)
                    if report:
                        self._save_report(report)
                        reports.append(report)
        
        return reports
    
    def _detect_vuln_type(self, text: str) -> Optional[str]:
        """Detect vulnerability type from text content."""
        text_lower = text.lower()
        
        vuln_patterns = [
            (r"idor|insecure direct object", "IDOR"),
            (r"sql.?injection|sqli", "SQL Injection"),
            (r"xss|cross.?site.?script", "XSS"),
            (r"ssrf|server.?side.?request", "SSRF"),
            (r"csrf|cross.?site.?request.?forgery", "CSRF"),
            (r"auth.?bypass|authentication.?bypass", "Authentication Bypass"),
            (r"broken.?access|access.?control", "Broken Access Control"),
            (r"race.?condition", "Race Condition"),
            (r"rce|remote.?code.?execution", "RCE"),
            (r"xxe|xml.?external", "XXE"),
            (r"path.?traversal|directory.?traversal", "Path Traversal"),
            (r"business.?logic", "Business Logic"),
            (r"information.?disclosure|info.?leak", "Information Disclosure"),
            (r"privilege.?escalation", "Privilege Escalation"),
            (r"open.?redirect", "Open Redirect"),
        ]
        
        for pattern, vuln_type in vuln_patterns:
            if re.search(pattern, text_lower):
                return vuln_type
        
        return None
    
    def scrape(self, max_reports: int = 40, progress: Optional[Progress] = None,
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape Bugcrowd disclosed reports.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of scraped reports
        """
        reports = []
        page = 1
        max_pages = 10
        
        console.print(f"[cyan]Scraping Bugcrowd disclosures (target: {max_reports} reports)...[/cyan]")
        
        # First try the disclosures page
        while len(reports) < max_reports and page <= max_pages:
            soup = self._fetch_disclosures_page(page)
            if not soup:
                break
            
            # Find disclosure cards
            cards = soup.find_all(class_=re.compile(r"disclosure|card", re.I))
            if not cards:
                cards = soup.find_all("article")
            if not cards:
                cards = soup.find_all("li", class_=re.compile(r"item", re.I))
            
            if not cards:
                break
            
            for card in cards:
                if len(reports) >= max_reports:
                    break
                
                card_data = self._parse_disclosure_card(card)
                if not card_data:
                    continue
                
                if self._report_exists(card_data["id"]):
                    continue
                
                # Fetch full details
                details = self._fetch_disclosure_details(card_data["url"])
                
                report = RawReport(
                    id=card_data["id"],
                    source=self.SOURCE_NAME,
                    title=card_data["title"],
                    url=card_data["url"],
                    severity=card_data["severity"],
                    affected_component=card_data.get("program"),
                    body=details.get("body") if details else None,
                    vuln_type=details.get("vuln_type") if details else None,
                    cwe=details.get("cwe") if details else None,
                    cvss_score=details.get("cvss_score") if details else None,
                )
                
                self._save_report(report)
                reports.append(report)
                
                if progress and task:
                    progress.update(task, advance=1)
            
            page += 1
        
        # Also scrape blog write-ups to supplement
        if len(reports) < max_reports:
            blog_reports = self._scrape_blog_writeups(max_reports - len(reports))
            reports.extend(blog_reports)
            
            if progress and task:
                progress.update(task, advance=len(blog_reports))
        
        console.print(f"[green]Scraped {len(reports)} new Bugcrowd reports[/green]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    
    with BugcrowdScraper(data_dir) as scraper:
        reports = scraper.scrape(max_reports=5)
        print(f"Scraped {len(reports)} reports")
        for r in reports[:3]:
            print(f"  - {r.title} ({r.severity})")
