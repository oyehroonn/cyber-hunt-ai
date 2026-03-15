"""
Proxy pool manager for CyberAI platform.
Scrapes and validates free proxies from multiple sources.
"""

import asyncio
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from cyberAI.config import get_config
from cyberAI.utils.helpers import atomic_write_json, load_json


class ProxyManager:
    """
    Manages a pool of validated proxies.
    Scrapes from multiple free proxy sources and validates them.
    """
    
    PROXY_SOURCES = [
        "https://free-proxy-list.net/",
        "https://www.sslproxies.org/",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    ]
    
    def __init__(self, cache_path: Optional[Path] = None, cache_ttl_minutes: int = 30):
        """
        Initialize the proxy manager.
        
        Args:
            cache_path: Path to cache validated proxies
            cache_ttl_minutes: How long to cache proxies before refreshing
        """
        config = get_config()
        self.cache_path = cache_path or config.get_output_path("proxies.json")
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._proxies: list[str] = []
        self._proxy_index = 0
        self._lock = asyncio.Lock()
    
    async def scrape_free_proxies(self) -> list[str]:
        """
        Scrape free proxies from multiple sources.
        
        Returns:
            List of proxy strings in host:port format
        """
        all_proxies: set[str] = set()
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for source_url in self.PROXY_SOURCES:
                try:
                    proxies = await self._scrape_source(client, source_url)
                    all_proxies.update(proxies)
                    logger.info(f"Scraped {len(proxies)} proxies from {source_url}")
                except Exception as e:
                    logger.warning(f"Failed to scrape {source_url}: {e}")
        
        logger.info(f"Total unique proxies scraped: {len(all_proxies)}")
        return list(all_proxies)
    
    async def _scrape_source(self, client: httpx.AsyncClient, url: str) -> list[str]:
        """Scrape proxies from a single source."""
        response = await client.get(url)
        response.raise_for_status()
        content = response.text
        
        if "proxyscrape.com" in url:
            return self._parse_plain_text(content)
        else:
            return self._parse_html_table(content)
    
    def _parse_html_table(self, html: str) -> list[str]:
        """Parse proxies from HTML table format (free-proxy-list, sslproxies)."""
        proxies = []
        soup = BeautifulSoup(html, "lxml")
        
        table = soup.find("table", class_="table")
        if not table:
            table = soup.find("table")
        
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    ip = cells[0].get_text(strip=True)
                    port = cells[1].get_text(strip=True)
                    if self._is_valid_ip(ip) and port.isdigit():
                        proxies.append(f"{ip}:{port}")
        
        return proxies
    
    def _parse_plain_text(self, text: str) -> list[str]:
        """Parse proxies from plain text format (one per line)."""
        proxies = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if ':' in line:
                parts = line.split(':')
                if len(parts) == 2 and self._is_valid_ip(parts[0]) and parts[1].isdigit():
                    proxies.append(line)
        return proxies
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    async def validate_proxies(
        self,
        proxies: list[str],
        test_url: str = "https://httpbin.org/ip",
        timeout: float = 5.0,
        max_concurrent: int = 50
    ) -> list[str]:
        """
        Validate proxies by testing them against a URL.
        
        Args:
            proxies: List of proxy strings to validate
            test_url: URL to test against
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent validation requests
            
        Returns:
            List of working proxy strings
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        valid_proxies: list[str] = []
        
        async def test_proxy(proxy: str) -> Optional[str]:
            async with semaphore:
                try:
                    async with httpx.AsyncClient(
                        proxies={"http://": f"http://{proxy}", "https://": f"http://{proxy}"},
                        timeout=timeout
                    ) as client:
                        response = await client.get(test_url)
                        if response.status_code == 200:
                            return proxy
                except Exception:
                    pass
                return None
        
        tasks = [test_proxy(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        
        valid_proxies = [p for p in results if p is not None]
        logger.info(f"Validated {len(valid_proxies)}/{len(proxies)} proxies")
        return valid_proxies
    
    async def get_proxy_pool(self, force_refresh: bool = False) -> list[str]:
        """
        Get the current pool of validated proxies.
        Uses cache if available and fresh.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            List of validated proxy strings
        """
        async with self._lock:
            if not force_refresh and self._proxies:
                return self._proxies
            
            if not force_refresh:
                cached = self._load_cache()
                if cached:
                    self._proxies = cached
                    return self._proxies
            
            logger.info("Refreshing proxy pool...")
            raw_proxies = await self.scrape_free_proxies()
            self._proxies = await self.validate_proxies(raw_proxies)
            
            self._save_cache(self._proxies)
            
            return self._proxies
    
    def _load_cache(self) -> Optional[list[str]]:
        """Load proxies from cache if fresh."""
        data = load_json(self.cache_path)
        if not data:
            return None
        
        cached_at = data.get("cached_at")
        if cached_at:
            try:
                cached_time = datetime.fromisoformat(cached_at)
                if datetime.utcnow() - cached_time < self.cache_ttl:
                    logger.info(f"Using cached proxies from {cached_at}")
                    return data.get("proxies", [])
            except ValueError:
                pass
        
        return None
    
    def _save_cache(self, proxies: list[str]) -> None:
        """Save proxies to cache."""
        data = {
            "cached_at": datetime.utcnow().isoformat(),
            "proxies": proxies,
            "count": len(proxies),
        }
        atomic_write_json(self.cache_path, data)
    
    async def get_next_proxy(self) -> Optional[str]:
        """
        Get the next proxy from the pool (round-robin).
        
        Returns:
            Proxy string or None if pool is empty
        """
        pool = await self.get_proxy_pool()
        if not pool:
            return None
        
        async with self._lock:
            proxy = pool[self._proxy_index % len(pool)]
            self._proxy_index += 1
            return proxy
    
    async def get_random_proxy(self) -> Optional[str]:
        """
        Get a random proxy from the pool.
        
        Returns:
            Proxy string or None if pool is empty
        """
        import random
        pool = await self.get_proxy_pool()
        if not pool:
            return None
        return random.choice(pool)
    
    def format_for_httpx(self, proxy: str) -> dict[str, str]:
        """
        Format a proxy string for use with httpx.
        
        Args:
            proxy: Proxy in host:port format
            
        Returns:
            Dict suitable for httpx proxies parameter
        """
        return {
            "http://": f"http://{proxy}",
            "https://": f"http://{proxy}",
        }
    
    def format_for_playwright(self, proxy: str) -> dict[str, str]:
        """
        Format a proxy string for use with Playwright.
        
        Args:
            proxy: Proxy in host:port format
            
        Returns:
            Dict suitable for Playwright proxy parameter
        """
        return {
            "server": f"http://{proxy}",
        }


_proxy_manager: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    """Get the global proxy manager instance."""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager


if __name__ == "__main__":
    async def main():
        manager = ProxyManager()
        
        print("Scraping proxies...")
        proxies = await manager.scrape_free_proxies()
        print(f"Found {len(proxies)} proxies")
        
        if proxies:
            print("\nValidating first 20 proxies...")
            valid = await manager.validate_proxies(proxies[:20])
            print(f"Valid proxies: {valid}")
    
    asyncio.run(main())
