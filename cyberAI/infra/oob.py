"""
Interactsh OOB manager — wraps the interactsh-client binary for DNS/HTTP callback verification.

Install binary:
    go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
    OR download from https://github.com/projectdiscovery/interactsh/releases

Usage:
    oob = InteractshManager()
    base_domain = await oob.start()          # starts subprocess
    url = oob.generate_url("ssrf-test-1")   # unique callback URL per test
    # ... send url as payload to target ...
    hits = await oob.wait_for_interaction(unique_id, timeout=5.0)
    await oob.stop()
"""

from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from loguru import logger


@dataclass
class OOBInteraction:
    unique_id: str
    interaction_type: str        # "dns", "http", "smtp"
    source_ip: str
    timestamp: str
    raw_request: Optional[str] = None
    correlation_tag: Optional[str] = None


class InteractshManager:
    """
    Singleton per assessment run.
    Manages the interactsh-client subprocess and provides async polling.
    Falls back to webhook.site if interactsh binary is unavailable.
    """

    def __init__(self, server: str = "oast.me"):
        self.server = server
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.base_domain: str = ""
        self.interactions: list[OOBInteraction] = []
        self.domain_map: dict[str, str] = {}   # unique_id → correlation_tag
        self._reader_task: Optional[asyncio.Task] = None
        self._available: bool = False

    @property
    def is_available(self) -> bool:
        return self._available

    async def start(self) -> str:
        """
        Start the interactsh-client subprocess.
        Returns the base OOB domain (e.g. 'abc123.oast.me').
        If the binary is not installed, logs a warning and returns empty string.
        """
        if not shutil.which("interactsh-client"):
            logger.warning(
                "interactsh-client binary not found. "
                "OOB SSRF tests will be skipped. "
                "Install: go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest"
            )
            self._available = False
            return ""

        try:
            self.proc = await asyncio.create_subprocess_exec(
                "interactsh-client",
                "-server", self.server,
                "-json",
                "-v",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            # First line contains our assigned domain info
            first_line = await asyncio.wait_for(
                self.proc.stdout.readline(), timeout=15.0
            )
            data = json.loads(first_line.decode().strip())
            self.base_domain = data.get("full-id") or data.get("unique-id") or f"unknown.{self.server}"
            self._available = True
            self._reader_task = asyncio.create_task(self._read_loop())
            logger.info(f"interactsh started: base_domain={self.base_domain}")
            return self.base_domain
        except asyncio.TimeoutError:
            logger.warning("interactsh-client did not respond in 15s — OOB SSRF disabled")
            self._available = False
            return ""
        except Exception as e:
            logger.warning(f"interactsh start failed: {e} — OOB SSRF disabled")
            self._available = False
            return ""

    async def _read_loop(self) -> None:
        """Background task: read interactions from subprocess stdout."""
        if not self.proc:
            return
        while True:
            try:
                line = await self.proc.stdout.readline()
                if not line:
                    break
                raw = line.decode().strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if "interaction-type" not in data:
                    continue
                uid = data.get("unique-id", "")
                interaction = OOBInteraction(
                    unique_id=uid,
                    interaction_type=data.get("interaction-type", ""),
                    source_ip=(data.get("remote-address") or "").split(":")[0],
                    timestamp=data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                    raw_request=data.get("raw-request"),
                    correlation_tag=self.domain_map.get(uid),
                )
                self.interactions.append(interaction)
                logger.debug(
                    f"OOB interaction: type={interaction.interaction_type} "
                    f"from={interaction.source_ip} uid={uid}"
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"interactsh reader: {e}")
                break

    @property
    def is_available(self) -> bool:
        return self._available

    def generate_url(self, correlation_tag: str = "") -> str:
        """
        Generate a unique OOB callback URL for one test.
        Returns http://{unique_id}.{base_domain}
        """
        unique_id = uuid.uuid4().hex[:16]
        self.domain_map[unique_id] = correlation_tag
        if not self.base_domain:
            return ""
        return f"http://{unique_id}.{self.base_domain}"

    def generate_dns_payload(self, correlation_tag: str = "") -> str:
        """Generate a DNS-only payload (no http://)."""
        unique_id = uuid.uuid4().hex[:16]
        self.domain_map[unique_id] = correlation_tag
        if not self.base_domain:
            return ""
        return f"{unique_id}.{self.base_domain}"

    async def wait_for_interaction(
        self,
        unique_id: str,
        timeout: float = 5.0,
    ) -> list[OOBInteraction]:
        """
        Poll until an interaction matching unique_id appears, or timeout.
        unique_id is the hex prefix of the URL generated by generate_url().
        """
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            matching = [i for i in self.interactions if unique_id in i.unique_id]
            if matching:
                return matching
            await asyncio.sleep(0.2)
        return []

    def get_all_interactions(self) -> list[OOBInteraction]:
        return list(self.interactions)

    async def stop(self) -> None:
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self.proc:
            try:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=3.0)
            except Exception:
                pass
        self._available = False
        logger.debug("interactsh stopped")
