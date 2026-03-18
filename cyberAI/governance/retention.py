"""
ASRTS §4.4: Data retention and TTL.
RetentionJob: read engagement config TTL; delete or redact WARC and structured outputs older than TTL.
"""

import time
from pathlib import Path
from typing import Optional

from loguru import logger

from cyberAI.config import get_config


def run_retention_job(
    engagement_config_path: Optional[str] = None,
    output_dir: Optional[Path] = None,
    raw_ttl_days: Optional[int] = None,
    structured_ttl_days: Optional[int] = None,
    dry_run: bool = False,
) -> dict:
    """
    Delete WARC and recon/test outputs older than TTL days.
    If engagement config is loaded, use its data_retention; else use raw_ttl_days/structured_ttl_days.
    Returns {"deleted": [...], "errors": [...]}.
    """
    config = get_config()
    out = output_dir or config.output_dir
    now = time.time()
    deleted: list[str] = []
    errors: list[str] = []

    try:
        from cyberAI.governance.loader import load_engagement_config
        engagement = load_engagement_config(engagement_config_path or config.engagement_config_path)
        if engagement and engagement.data_retention:
            raw_ttl_days = raw_ttl_days if raw_ttl_days is not None else engagement.data_retention.raw_capture_ttl_days
            structured_ttl_days = structured_ttl_days if structured_ttl_days is not None else engagement.data_retention.structured_ttl_days
    except Exception as e:
        logger.debug(f"Retention: load engagement config: {e}")

    raw_ttl_days = raw_ttl_days if raw_ttl_days is not None else 90
    structured_ttl_days = structured_ttl_days if structured_ttl_days is not None else 365
    raw_cutoff = now - (raw_ttl_days * 86400)
    struct_cutoff = now - (structured_ttl_days * 86400)

    # WARC: outputs/warc/
    warc_dir = out / "warc"
    if warc_dir.exists():
        for f in warc_dir.rglob("*"):
            if f.is_file():
                try:
                    if f.stat().st_mtime < raw_cutoff:
                        if not dry_run:
                            f.unlink()
                        deleted.append(str(f))
                except Exception as e:
                    errors.append(f"{f}: {e}")

    # Structured: recon, planning, testing findings, reports (older than structured_ttl_days)
    for sub in ("recon", "planning", "testing", "reports", "logs"):
        d = out / sub
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file():
                try:
                    if f.stat().st_mtime < struct_cutoff:
                        if not dry_run:
                            f.unlink()
                        deleted.append(str(f))
                except Exception as e:
                    errors.append(f"{f}: {e}")

    logger.info(f"Retention: deleted {len(deleted)} items" + (" (dry run)" if dry_run else ""))
    return {"deleted": deleted, "errors": errors, "dry_run": dry_run}
