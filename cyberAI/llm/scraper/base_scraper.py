"""
Base Scraper Class

Provides common functionality for all scrapers:
- Rate limiting
- Retry logic
- File I/O
- Progress tracking
"""

import json
import time
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

import httpx
from rich.console import Console
from rich.progress import Progress, TaskID
from pydantic import BaseModel, Field

console = Console()


class RawReport(BaseModel):
    """Base schema for raw scraped reports."""
    id: str
    source: str
    title: str
    url: str
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: Optional[str] = None
    vuln_type: Optional[str] = None
    cwe: Optional[str] = None
    cvss_score: Optional[float] = None
    affected_component: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    bounty: Optional[float] = None
    disclosed_at: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base class for security report scrapers."""
    
    SOURCE_NAME: str = "unknown"
    REQUEST_DELAY: float = 1.0  # Seconds between requests
    MAX_RETRIES: int = 3
    TIMEOUT: float = 30.0
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.client: Optional[httpx.Client] = None
        self.async_client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0
    
    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.Client(
                timeout=self.TIMEOUT,
                follow_redirects=True,
                headers={
                    "User-Agent": "SecurityResearchBot/1.0 (Authorized Security Testing)",
                    "Accept": "text/html,application/json,application/xhtml+xml",
                }
            )
        return self.client
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()
    
    def _fetch_with_retry(self, url: str, raise_on_error: bool = False, **kwargs) -> Optional[httpx.Response]:
        """
        Fetch URL with retry logic and rate limiting.
        
        Args:
            url: URL to fetch
            raise_on_error: If True, raise exceptions instead of returning None
            **kwargs: Additional arguments to pass to httpx.get
            
        Returns:
            Response object or None on failure
        """
        self._rate_limit()
        client = self._get_client()
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = client.get(url, **kwargs)
                
                # For successful responses, return immediately
                if response.status_code == 200:
                    return response
                
                # Handle various error codes
                if response.status_code == 429:  # Rate limited
                    wait_time = 2 ** (attempt + 2)
                    console.print(f"[yellow]Rate limited, waiting {wait_time}s...[/yellow]")
                    time.sleep(wait_time)
                    continue
                elif response.status_code in (403, 404, 410):  # Gone/Forbidden/Not Found
                    # Don't spam console for expected failures
                    return response  # Return response so caller can check status_code
                elif response.status_code >= 500:  # Server error - retry
                    wait_time = 2 ** attempt
                    console.print(f"[yellow]Server error {response.status_code}, retry in {wait_time}s[/yellow]")
                    time.sleep(wait_time)
                    continue
                else:
                    # Other 4xx errors - return the response
                    return response
                    
            except httpx.HTTPStatusError as e:
                if raise_on_error:
                    raise
                console.print(f"[red]HTTP error for {url}: {e}[/red]")
            except httpx.RequestError as e:
                if raise_on_error and attempt == self.MAX_RETRIES - 1:
                    raise
                wait_time = 2 ** attempt
                if attempt < self.MAX_RETRIES - 1:
                    console.print(f"[dim]Request error, retry {attempt + 1}/{self.MAX_RETRIES}...[/dim]")
                    time.sleep(wait_time)
            except Exception as e:
                if raise_on_error:
                    raise
                console.print(f"[red]Unexpected error fetching {url}: {e}[/red]")
                break
        
        return None
    
    def _report_exists(self, report_id: str) -> bool:
        """Check if report already exists (for resumability)."""
        filename = f"{self.SOURCE_NAME}_{report_id}.json"
        return (self.raw_dir / filename).exists()
    
    def _save_report(self, report: RawReport) -> Path:
        """Save a raw report to disk."""
        filename = f"{self.SOURCE_NAME}_{report.id}.json"
        filepath = self.raw_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID from content hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    @abstractmethod
    def scrape(self, max_reports: int = 100, progress: Optional[Progress] = None, 
               task: Optional[TaskID] = None) -> list[RawReport]:
        """
        Scrape reports from the source.
        
        Args:
            max_reports: Maximum number of reports to scrape
            progress: Rich progress bar (optional)
            task: Task ID for progress tracking (optional)
            
        Returns:
            List of scraped reports
        """
        pass
    
    def get_existing_count(self) -> int:
        """Count existing reports from this source."""
        pattern = f"{self.SOURCE_NAME}_*.json"
        return len(list(self.raw_dir.glob(pattern)))
    
    def close(self):
        """Clean up resources."""
        if self.client:
            self.client.close()
            self.client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
