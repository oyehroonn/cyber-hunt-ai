"""
ASRTS session store: in-memory + JSON persist (no Redis).
Key: (engagement_id, role). Value: cookies dict + optional auth headers.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.utils.helpers import atomic_write_json, load_json


class SessionStore:
    """
    Store session cookies and headers per (engagement_id, role).
    Persists to outputs/sessions/sessions.json when path is set.
    """

    def __init__(self, persist_path: Optional[Path] = None):
        self._store: dict[str, dict[str, dict[str, Any]]] = {}  # engagement_id -> role -> data
        self._persist_path = Path(persist_path) if persist_path else None
        self.load()

    def _key(self, engagement_id: str, role: str) -> tuple[str, str]:
        return (engagement_id or "default", role or "default")

    def get(self, engagement_id: str, role: str) -> Optional[dict[str, Any]]:
        """Return session data (cookies, headers, updated_at) or None."""
        eng = self._store.get(engagement_id or "default")
        if not eng:
            return None
        return eng.get(role or "default")

    def set(
        self,
        engagement_id: str,
        role: str,
        cookies: dict[str, str],
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Store session for (engagement_id, role)."""
        eng = engagement_id or "default"
        r = role or "default"
        if eng not in self._store:
            self._store[eng] = {}
        self._store[eng][r] = {
            "cookies": dict(cookies),
            "headers": dict(headers or {}),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def invalidate(self, engagement_id: str, role: str) -> None:
        """Remove session for (engagement_id, role)."""
        eng = engagement_id or "default"
        r = role or "default"
        if eng in self._store and r in self._store[eng]:
            del self._store[eng][r]
            self.save()

    def save(self) -> None:
        """Persist to JSON."""
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self._persist_path, {"sessions": self._store})
        except Exception as e:
            logger.debug(f"Session store save: {e}")

    def load(self) -> None:
        """Load from JSON if path exists."""
        if not self._persist_path or not self._persist_path.is_file():
            return
        try:
            data = load_json(self._persist_path)
            if data and "sessions" in data:
                self._store = data["sessions"]
        except Exception as e:
            logger.debug(f"Session store load: {e}")
