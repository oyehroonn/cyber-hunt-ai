"""
Per-host and optional global rate limiter for polite crawling.

Token-bucket style: acquire(host) blocks until a token is available.
"""

import asyncio
import time
from collections import defaultdict
from typing import Optional

from loguru import logger

from cyberAI.governance.schema import EngagementConfig, RateLimits


class RateLimiter:
    """
    Async rate limiter: per-host RPS and optional global RPS.
    Uses a simple sliding-window style: track last N request times per key.
    """

    def __init__(self, limits: Optional[RateLimits] = None):
        self._limits = limits or RateLimits()
        self._per_host: dict[str, list[float]] = defaultdict(list)
        self._global_times: list[float] = []
        self._lock = asyncio.Lock()

    def _trim_old(self, times: list[float], window_sec: float) -> None:
        """Remove timestamps older than window."""
        cutoff = time.monotonic() - window_sec
        while times and times[0] < cutoff:
            times.pop(0)

    async def acquire(self, host: str) -> None:
        """
        Block until a request is allowed for this host (and globally if configured).
        Call this before every outbound request.
        """
        async with self._lock:
            now = time.monotonic()
            window = 1.0  # 1 second window for RPS

            self._trim_old(self._per_host[host], window)
            self._trim_old(self._global_times, window)

            per_host_rps = max(0.1, self._limits.per_host_rps)
            if len(self._per_host[host]) >= per_host_rps:
                sleep_for = window - (now - self._per_host[host][0])
                if sleep_for > 0:
                    logger.debug(f"Rate limit sleep {sleep_for:.2f}s for host {host}")
                    await asyncio.sleep(sleep_for)
                    now = time.monotonic()
                    self._trim_old(self._per_host[host], window)

            global_rps = self._limits.global_rps
            if global_rps is not None and global_rps > 0:
                self._trim_old(self._global_times, window)
                if len(self._global_times) >= global_rps:
                    sleep_for = window - (now - self._global_times[0])
                    if sleep_for > 0:
                        await asyncio.sleep(sleep_for)
                        now = time.monotonic()
                        self._trim_old(self._global_times, window)
                self._global_times.append(now)

            self._per_host[host].append(now)

    @classmethod
    def from_engagement(cls, config: Optional[EngagementConfig]) -> Optional["RateLimiter"]:
        """Build RateLimiter from engagement config; None if no config."""
        if config is None:
            return None
        return cls(config.rate_limits)


_global_limiter: Optional[RateLimiter] = None


def set_global_rate_limiter(limiter: Optional[RateLimiter]) -> None:
    """Set the global rate limiter (used by http_client)."""
    global _global_limiter
    _global_limiter = limiter


def get_global_rate_limiter() -> Optional[RateLimiter]:
    """Get the global rate limiter."""
    return _global_limiter
