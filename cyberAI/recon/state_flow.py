"""
ASRTS §2.3: State-flow crawling (Crawljax-style).
DOM hash → state_id; fire click/submit events; record transitions; cap total states.
"""

import asyncio
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from cyberAI.recon.network_intelligence import NetworkIntelligence

from loguru import logger
from playwright.async_api import BrowserContext, Page

from cyberAI.config import get_config
from cyberAI.models import CrawlState, CrawlTransition
from cyberAI.utils.browser import get_page_actions, wait_for_network_idle
from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json, safe_filename

# JS to get canonical DOM string: body without script/style, normalized
_DOM_SCRIPT = """
() => {
  const clone = document.body ? document.body.cloneNode(true) : document.documentElement.cloneNode(true);
  clone.querySelectorAll('script, style, noscript').forEach(el => el.remove());
  clone.querySelectorAll('[data-reactroot], [data-id]').forEach(el => {
    el.removeAttribute('data-reactroot');
    el.removeAttribute('data-id');
  });
  const html = clone.innerHTML.replace(/\\s+/g, ' ').trim();
  return html.length > 50000 ? html.substring(0, 50000) : html;
}
"""


def _dom_hash(html: str) -> str:
    """SHA-256 of normalized DOM string."""
    normalized = re.sub(r"\s+", " ", html).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _simhash(html: str, bits: int = 64) -> int:
    """
    64-bit SimHash of text for merging similar DOM states (ASRTS §5).
    Uses word-level shingles; similar DOMs get similar hashes.
    """
    normalized = re.sub(r"\s+", " ", (html or "").strip())
    if len(normalized) < 10:
        return 0
    # Shingle by 5-char windows
    shingles = [normalized[i : i + 5] for i in range(0, min(len(normalized) - 4, 2000), 3)]
    vec = [0] * bits
    for s in shingles:
        h = int(hashlib.md5(s.encode("utf-8", errors="replace")).hexdigest()[:16], 16)
        for i in range(bits):
            if (h >> i) & 1:
                vec[i] += 1
            else:
                vec[i] -= 1
    out = 0
    for i in range(bits):
        if vec[i] > 0:
            out |= 1 << i
    return out


def _hamming(a: int, b: int, bits: int = 64) -> int:
    x = a ^ b
    return bin(x).count("1") if x >= 0 else bits


SIMHASH_MERGE_THRESHOLD = 3  # Merge states if SimHash Hamming distance <= this


class StateFlowCrawler:
    """
    Crawljax-style state-flow explorer: DOM hash states, fire events, record transitions.
    Cap total states (default 2000).
    """

    def __init__(
        self,
        run_id: Optional[str] = None,
        max_states: int = 2000,
        network_idle_timeout_ms: int = 2000,
        action_delay_ms: int = 800,
    ):
        self.config = get_config()
        self.run_id = run_id or ""
        self._max_states = max_states
        self._network_idle_timeout = network_idle_timeout_ms
        self._action_delay = action_delay_ms
        self._states: dict[str, CrawlState] = {}
        self._transitions: list[CrawlTransition] = []
        self._seen_hashes: set[str] = set()
        self._state_simhash: dict[str, int] = {}  # state_id -> SimHash bits (for merging)

    async def _get_dom_html(self, page: Page) -> str:
        try:
            return await page.evaluate(_DOM_SCRIPT) or ""
        except Exception as e:
            logger.debug(f"DOM script failed: {e}")
            return ""

    async def _get_dom_hash(self, page: Page) -> str:
        html = await self._get_dom_html(page)
        return _dom_hash(html)

    def _resolve_state_id(self, html: str, url: str) -> tuple[str, bool]:
        """
        Return (state_id, is_new). Use SHA for exact match; SimHash to merge similar states.
        """
        sha = _dom_hash(html)
        sim = _simhash(html)
        if sha in self._seen_hashes:
            for sid, s in self._state_simhash.items():
                if _hamming(sim, s) <= SIMHASH_MERGE_THRESHOLD:
                    return sid, False
            return f"s_{sha}", False
        for sid, s in self._state_simhash.items():
            if _hamming(sim, s) <= SIMHASH_MERGE_THRESHOLD:
                self._seen_hashes.add(sha)
                return sid, False
        state_id = f"s_{sha}"
        self._seen_hashes.add(sha)
        self._state_simhash[state_id] = sim
        return state_id, True

    async def _replay_path(
        self,
        page: Page,
        start_url: str,
        path: list[tuple[str, str, Optional[str]]],
    ) -> bool:
        """Replay a sequence of (action_type, selector, href_or_action) to reach a state."""
        await page.goto(start_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(0.5)
        for action_type, selector, extra in path:
            try:
                if action_type == "navigate" and extra:
                    await page.goto(extra, wait_until="domcontentloaded", timeout=10000)
                elif action_type == "click" and selector:
                    await page.click(selector, timeout=3000)
                elif action_type == "submit" and selector:
                    await page.locator(selector).first.evaluate("el => el.submit()")
                await wait_for_network_idle(page, self._network_idle_timeout)
                await asyncio.sleep(self._action_delay / 1000.0)
            except Exception as e:
                logger.debug(f"Replay step failed: {e}")
                return False
        return True

    async def run(
        self,
        context: BrowserContext,
        start_url: str,
        network_intel: Optional["NetworkIntelligence"] = None,
        routes_to_expand: Optional[list[str]] = None,
    ) -> tuple[list[CrawlState], list[CrawlTransition]]:
        """
        Run state-flow exploration from start_url (and optionally from routes_to_expand URLs).
        Returns (states, transitions). New requests are captured if network_intel is attached to context.
        """
        if network_intel:
            await network_intel.attach_to_context(context, None)

        page = await context.new_page()
        try:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=15000)
            await wait_for_network_idle(page, self._network_idle_timeout)
            initial_html = await self._get_dom_html(page)
            if not initial_html:
                return list(self._states.values()), self._transitions

            initial_id, is_new = self._resolve_state_id(initial_html, start_url)
            if is_new:
                self._states[initial_id] = CrawlState(
                    state_id=initial_id,
                    dom_hash=_dom_hash(initial_html),
                    url=start_url,
                    discovered_at=datetime.utcnow(),
                )

            # Frontier: (state_id, path) where path = list of (type, selector, href/action)
            frontier: list[tuple[str, list[tuple[str, str, Optional[str]]]]] = [
                (initial_id, [])
            ]

            while frontier and len(self._states) < self._max_states:
                state_id, path = frontier.pop(0)
                replayed = await self._replay_path(page, start_url, path)
                if not replayed:
                    continue

                current_html = await self._get_dom_html(page)
                state_id, _ = self._resolve_state_id(current_html, page.url)
                if state_id not in self._states:
                    self._states[state_id] = CrawlState(
                        state_id=state_id,
                        dom_hash=_dom_hash(current_html),
                        url=page.url,
                        discovered_at=datetime.utcnow(),
                    )

                raw_actions = await get_page_actions(page)
                for a in raw_actions:
                    if len(self._states) >= self._max_states:
                        break
                    action_type = a.get("type", "click")
                    selector = a.get("selector", "")
                    href = a.get("href")
                    action_url = a.get("action")
                    if action_type == "navigate" and href:
                        extra: Optional[str] = href
                    elif action_type == "submit":
                        extra = action_url
                    else:
                        extra = None

                    if not selector and not extra and action_type != "navigate":
                        continue

                    # Replay path again so we're at state_id before each action
                    await self._replay_path(page, start_url, path)

                    try:
                        if action_type == "navigate" and extra:
                            await page.goto(extra, wait_until="domcontentloaded", timeout=10000)
                        elif action_type == "click" and selector:
                            await page.click(selector, timeout=3000)
                        elif action_type == "submit" and selector:
                            await page.locator(selector).first.evaluate("el => el.submit()")
                        else:
                            continue
                    except Exception as e:
                        logger.debug(f"Action failed: {e}")
                        continue

                    await wait_for_network_idle(page, self._network_idle_timeout)
                    await asyncio.sleep(self._action_delay / 1000.0)

                    new_html = await self._get_dom_html(page)
                    new_id, is_new = self._resolve_state_id(new_html, page.url)
                    if new_id == state_id:
                        continue
                    if is_new:
                        self._states[new_id] = CrawlState(
                            state_id=new_id,
                            dom_hash=_dom_hash(new_html),
                            url=page.url,
                            discovered_at=datetime.utcnow(),
                        )
                    self._transitions.append(
                        CrawlTransition(
                            from_state_id=state_id,
                            to_state_id=new_id,
                            event_type=action_type,
                            selector=selector or None,
                            payload_preview=extra[:200] if extra else None,
                        )
                    )
                    new_path = path + [(action_type, selector or "", extra)]
                    frontier.append((new_id, new_path))

            return list(self._states.values()), self._transitions
        finally:
            await page.close()

    def save(
        self,
        output_dir: Optional[Path] = None,
        run_id: Optional[str] = None,
    ) -> str:
        """Persist states and transitions to JSON."""
        run_id = run_id or self.run_id
        out = output_dir or self.config.output_dir
        path = out / "recon" / "intelligence" / "state_flow.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = add_meta_to_output(
            {
                "states": [s.model_dump() for s in self._states.values()],
                "transitions": [t.model_dump() for t in self._transitions],
            },
            target_url=getattr(self.config, "target_url", "") or "",
            phase="recon",
            run_id=run_id,
        )
        atomic_write_json(path, data)
        logger.info(f"State-flow: saved {len(self._states)} states, {len(self._transitions)} transitions")
        return str(path)


async def run_state_flow_crawl(
    context: BrowserContext,
    start_url: str,
    run_id: Optional[str] = None,
    network_intel: Optional["NetworkIntelligence"] = None,
    max_states: int = 2000,
) -> tuple[list[CrawlState], list[CrawlTransition]]:
    """Convenience: run StateFlowCrawler and return states/transitions."""
    crawler = StateFlowCrawler(run_id=run_id, max_states=max_states)
    states, transitions = await crawler.run(
        context, start_url, network_intel=network_intel
    )
    crawler.save(run_id=run_id)
    return states, transitions
