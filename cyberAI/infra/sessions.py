"""
SessionPool — manages multiple authenticated sessions for security testing.

Each session stores: email, password, jwt, user_id, role, created_at.
Provides HTTP clients pre-configured with auth headers.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Optional

import httpx
from loguru import logger


class SessionPool:
    """
    Maintains a pool of authenticated sessions keyed by name.
    e.g. {"user_a": {...}, "user_b": {...}, "admin": {...}}
    """

    def __init__(self, target_url: str):
        self.target_url = target_url.rstrip("/")
        self._sessions: dict[str, dict] = {}

    def add(self, name: str, session: dict) -> None:
        """Add or update a session."""
        self._sessions[name] = session
        logger.debug(f"session_pool: added {name} (user_id={session.get('user_id')})")

    def get(self, name: str) -> Optional[dict]:
        return self._sessions.get(name)

    def all(self) -> dict[str, dict]:
        return dict(self._sessions)

    def names(self) -> list[str]:
        return list(self._sessions.keys())

    def has(self, name: str) -> bool:
        return name in self._sessions and bool(self._sessions[name].get("jwt"))

    def get_jwt(self, name: str) -> Optional[str]:
        s = self._sessions.get(name, {})
        return s.get("jwt") or s.get("token")

    def make_client(self, session_name: Optional[str] = None, timeout: float = 30.0) -> httpx.AsyncClient:
        """
        Create an httpx.AsyncClient pre-configured with auth headers for the given session.
        If session_name is None, returns an unauthenticated client.
        """
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if session_name:
            jwt = self.get_jwt(session_name)
            if jwt:
                headers["Authorization"] = f"Bearer {jwt}"
        return httpx.AsyncClient(
            base_url=self.target_url,
            headers=headers,
            timeout=timeout,
            verify=False,
            follow_redirects=False,
        )

    def decode_jwt_payload(self, session_name: str) -> Optional[dict]:
        """Decode the JWT payload (base64) without verification."""
        jwt = self.get_jwt(session_name)
        if not jwt:
            return None
        try:
            parts = jwt.split(".")
            if len(parts) < 2:
                return None
            payload_b64 = parts[1]
            # Add padding
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            return json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        except Exception:
            return None

    def get_user_id_from_jwt(self, session_name: str) -> Optional[Any]:
        """Extract user ID from JWT payload (tries 'sub', 'id', 'userId')."""
        payload = self.decode_jwt_payload(session_name)
        if not payload:
            session = self._sessions.get(session_name, {})
            return session.get("user_id")
        for key in ("sub", "id", "userId", "user_id", "uid"):
            if key in payload:
                return payload[key]
        return None

    def to_dict(self) -> dict:
        """Return sessions dict (for state serialization, omit full JWTs)."""
        result = {}
        for name, s in self._sessions.items():
            result[name] = {
                "email": s.get("email", ""),
                "user_id": s.get("user_id"),
                "role": s.get("role", "user"),
                "jwt": s.get("jwt", "")[:20] + "..." if s.get("jwt") else "",
            }
        return result

    def from_state(self, sessions_state: dict) -> None:
        """Restore sessions from state dict (includes full JWT)."""
        for name, s in sessions_state.items():
            self._sessions[name] = s

    def __len__(self) -> int:
        return len(self._sessions)
