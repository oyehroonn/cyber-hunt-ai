"""
ASRTS session health check and repair runner.
Uses HTTP GET to session_check_url; on 401/403 or redirect-to-login, trigger repair.
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from cyberAI.identity.session_store import SessionStore
from cyberAI.identity.login_sequence import LoginSequence, LoginRunner, load_login_sequence


class SessionHealthChecker:
    """
    Check if a session is still valid by requesting session_check_url with session cookies.
    """

    def __init__(self, session_check_url: str):
        self._check_url = session_check_url

    async def is_healthy(self, cookies: dict[str, str]) -> bool:
        """
        Perform GET to session_check_url with cookies. Return True if session looks valid.
        Valid = 200 and no redirect to common login paths.
        """
        try:
            import httpx
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                resp = await client.get(self._check_url, cookies=cookies)
            if resp.status_code in (401, 403):
                return False
            final_url = str(resp.url).lower()
            if any(x in final_url for x in ["/login", "signin", "auth", "sign-in"]):
                return False
            return True
        except Exception as e:
            logger.debug(f"Session health check failed: {e}")
            return False


class SessionRepairRunner:
    """
    Re-run login sequence and update session store on success.
    """

    def __init__(
        self,
        store: SessionStore,
        engagement_id: str,
        role: str,
        login_sequence: Optional[LoginSequence] = None,
        login_sequence_path: Optional[Path] = None,
        credentials: Optional[dict[str, str]] = None,
    ):
        self._store = store
        self._engagement_id = engagement_id
        self._role = role
        self._sequence = login_sequence or (load_login_sequence(login_sequence_path) if login_sequence_path else None)
        self._credentials = credentials or {}

    async def run(self, page) -> bool:
        """
        Execute login sequence on the given Playwright page.
        On success, update session store and return True. Else False.
        """
        if not self._sequence:
            logger.warning("No login sequence configured for session repair")
            return False
        runner = LoginRunner(self._credentials)
        result = await runner.run(self._sequence, page)
        if result:
            self._store.set(
                self._engagement_id,
                self._role,
                result["cookies"],
                result.get("headers"),
            )
            logger.info(f"Session repaired for {self._engagement_id}/{self._role}")
            return True
        return False
