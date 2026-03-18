"""
ASRTS: Populate SessionStore by running login for each configured role.
Uses LoginRunner + optional engagement test_identities (login_sequence_ref).
No Kafka/Redis; file-backed SessionStore only.
"""

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import Config, get_config
from cyberAI.identity.login_sequence import LoginRunner, load_login_sequence
from cyberAI.identity.session_store import SessionStore


def _resolve_login_sequence(
    role: str,
    login_sequence_ref: Optional[str],
    engagement_config_path: Optional[str],
    config: Config,
) -> Optional[Any]:
    """Resolve LoginSequence for role: from engagement ref or default path."""
    if login_sequence_ref:
        base = Path(engagement_config_path).parent if engagement_config_path else config.output_dir
        path = (base / login_sequence_ref).resolve()
        seq = load_login_sequence(path)
        if seq:
            return seq
    # Default: try recon/intelligence/login_{role}.json or login_sequence.json
    for name in (f"login_{role}.json", "login_sequence.json"):
        p = config.get_output_path("recon", "intelligence", name)
        if p and p.is_file():
            seq = load_login_sequence(p)
            if seq:
                return seq
    return None


async def ensure_sessions_for_roles(
    browser_pool: Any,
    config: Optional[Config] = None,
    engagement_id: Optional[str] = None,
    target_url: Optional[str] = None,
) -> int:
    """
    For each role in config.role_accounts, run login (if sequence available) and save to SessionStore.
    Returns number of sessions successfully populated.
    """
    config = config or get_config()
    engagement_id = engagement_id or config.run_id or "default"
    target_url = (target_url or config.target_url or "").rstrip("/") or "about:blank"

    try:
        from cyberAI.governance.loader import load_engagement_config
        engagement = load_engagement_config(config.engagement_config_path)
    except ImportError:
        engagement = None

    # Map role -> login_sequence_ref from engagement
    role_to_ref: dict[str, Optional[str]] = {}
    if engagement and engagement.test_identities:
        for ti in engagement.test_identities:
            role_to_ref[ti.role] = ti.login_sequence_ref

    store_path = config.get_output_path("sessions", "sessions.json")
    store = SessionStore(store_path)
    count = 0

    for acc in config.role_accounts:
        credentials = {"username": acc.username, "password": acc.password}
        login_sequence_ref = role_to_ref.get(acc.role)
        sequence = _resolve_login_sequence(
            acc.role,
            login_sequence_ref,
            config.engagement_config_path,
            config,
        )
        if not sequence or not sequence.steps:
            logger.debug(f"No login sequence for role {acc.role}; skip session populate")
            continue

        context = await browser_pool.get_browser_context(role=acc.role)
        page = await context.new_page()
        try:
            runner = LoginRunner(credentials)
            result = await runner.run(sequence, page)
            if result:
                store.set(
                    engagement_id,
                    acc.role,
                    result.get("cookies", {}),
                    result.get("headers"),
                )
                count += 1
                logger.info(f"Session populated for role {acc.role}")
            else:
                logger.warning(f"Login failed for role {acc.role}")
        finally:
            await page.close()
            await context.close()

    return count
