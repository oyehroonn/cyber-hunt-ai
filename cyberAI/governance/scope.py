"""
Scope validator: every outbound request must pass is_in_scope before being sent.

Pre-compiles allowed domains and out-of-scope patterns for fast synchronous checks.
"""

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from loguru import logger

from cyberAI.governance.schema import EngagementConfig


class ScopeValidator:
    """
    Validates URLs against engagement config.
    Returns (allowed: bool, reason: str). Out-of-scope requests are dropped and logged.
    """

    def __init__(self, config: EngagementConfig):
        self._config = config
        self._allowed_domains: list[str] = []
        self._allowed_netlocs: set[str] = set()
        self._out_of_scope: list[re.Pattern[str]] = []
        self._compile()

    def _compile(self) -> None:
        """Pre-compile domain and pattern checks."""
        for raw in self._config.target_domains:
            raw = raw.rstrip("/")
            try:
                parsed = urlparse(raw)
                if parsed.netloc:
                    self._allowed_netlocs.add(parsed.netloc.lower())
                    # www vs non-www: allow both
                    if parsed.netloc.lower().startswith("www."):
                        self._allowed_netlocs.add(parsed.netloc.lower().removeprefix("www."))
                    else:
                        self._allowed_netlocs.add("www." + parsed.netloc.lower())
            except Exception:
                pass
        for pattern in self._config.out_of_scope_patterns:
            try:
                # Treat as regex; escape simple glob * to .*
                re_pattern = pattern.replace(".", r"\.").replace("*", ".*")
                self._out_of_scope.append(re.compile(re_pattern, re.IGNORECASE))
            except re.error:
                logger.debug(f"Invalid out-of-scope pattern skipped: {pattern}")

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Strip fragment, sort query params for consistent matching."""
        try:
            parsed = urlparse(url)
            query = parse_qs(parsed.query, keep_blank_values=True)
            sorted_query = urlencode(sorted(query.items()), doseq=True)
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                sorted_query,
                "",  # no fragment
            ))
        except Exception:
            return url

    def is_in_scope(self, url: str, method: str = "GET") -> tuple[bool, str]:
        """
        Check if URL is within engagement scope.

        Returns:
            (True, "ok") if allowed; (False, reason) if out of scope.
        """
        if self._config.is_empty_scope():
            return True, "ok"

        try:
            parsed = urlparse(url)
            scheme = (parsed.scheme or "https").lower()
            if scheme not in self._config.allowed_schemes:
                return False, "scheme_not_allowed"

            netloc = (parsed.netloc or "").lower()
            if not netloc:
                return False, "no_netloc"

            # Allow www / non-www match
            if netloc not in self._allowed_netlocs:
                # Check if domain is a suffix of any allowed (e.g. subdomain)
                if not any(
                    netloc == n or netloc.endswith("." + n)
                    for n in self._allowed_netlocs
                ):
                    return False, "domain_out_of_scope"

            full_url = self._normalize_url(url)
            for pat in self._out_of_scope:
                if pat.search(full_url):
                    return False, "out_of_scope_pattern"

            return True, "ok"
        except Exception as e:
            logger.debug(f"Scope check error for {url}: {e}")
            return False, "error"

    def get_config(self) -> EngagementConfig:
        """Return the underlying engagement config."""
        return self._config


# Module-level validator set by main/config when engagement is loaded
_validator: ScopeValidator | None = None


def set_scope_validator(validator: ScopeValidator | None) -> None:
    """Set the global scope validator (used by http_client and browser)."""
    global _validator
    _validator = validator


def get_scope_validator() -> ScopeValidator | None:
    """Get the global scope validator; None if no engagement config loaded."""
    return _validator
