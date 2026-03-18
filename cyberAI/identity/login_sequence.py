"""
ASRTS login sequence: model and Playwright-based runner.
Steps: navigate, fill, click, wait_for_selector, assert_url_contains.
"""

import asyncio
from pathlib import Path
from typing import Any, Literal, Optional

from loguru import logger
from pydantic import BaseModel, Field


class LoginStep(BaseModel):
    """Single step in a login sequence."""
    action: Literal["navigate", "fill", "click", "wait", "assert_url_contains"]
    selector: Optional[str] = None
    value_ref: Optional[str] = None  # e.g. "username", "password" - resolved from credentials
    value: Optional[str] = None  # literal value
    url: Optional[str] = None  # for navigate or assert_url_contains
    timeout_ms: int = 10000


class LoginSequence(BaseModel):
    """Ordered list of steps to perform login."""
    steps: list[LoginStep] = Field(default_factory=list)
    success_url_contains: Optional[str] = None  # if URL contains this, login succeeded
    success_selector: Optional[str] = None  # or this selector visible


class LoginRunner:
    """
    Run a LoginSequence in Playwright and return cookies + headers on success.
    """

    def __init__(self, credentials: dict[str, str]):
        """
        Args:
            credentials: e.g. {"username": "u", "password": "p"} for value_ref resolution.
        """
        self._credentials = credentials

    async def run(self, sequence: LoginSequence, page) -> Optional[dict[str, Any]]:
        """
        Execute steps on the given Playwright page. On success, return
        {"cookies": {...}, "headers": {...}}. On failure, return None.
        """
        try:
            for step in sequence.steps:
                if step.action == "navigate" and step.url:
                    await page.goto(step.url, timeout=step.timeout_ms)
                elif step.action == "fill" and step.selector:
                    val = self._resolve_value(step)
                    if val is not None:
                        await page.fill(step.selector, val, timeout=step.timeout_ms)
                elif step.action == "click" and step.selector:
                    await page.click(step.selector, timeout=step.timeout_ms)
                elif step.action == "wait" and step.selector:
                    await page.wait_for_selector(step.selector, timeout=step.timeout_ms)
                elif step.action == "assert_url_contains" and step.url:
                    if step.url not in page.url:
                        logger.warning(f"Login assert failed: URL does not contain {step.url}")
                        return None
                await asyncio.sleep(0.5)

            # Success: extract cookies
            cookies_list = await page.context.cookies()
            cookies = {c["name"]: c["value"] for c in cookies_list}
            headers = {}
            # Optional: extract Authorization from page if set via JS
            return {"cookies": cookies, "headers": headers}
        except Exception as e:
            logger.warning(f"Login sequence failed: {e}")
            return None

    def _resolve_value(self, step: LoginStep) -> Optional[str]:
        if step.value is not None:
            return step.value
        if step.value_ref and step.value_ref in self._credentials:
            return self._credentials[step.value_ref]
        return None


def load_login_sequence(path: str | Path) -> Optional[LoginSequence]:
    """Load LoginSequence from JSON file."""
    from cyberAI.utils.helpers import load_json
    p = Path(path)
    if not p.is_file():
        return None
    data = load_json(p)
    if not data:
        return None
    try:
        return LoginSequence.model_validate(data)
    except Exception as e:
        logger.warning(f"Invalid login sequence at {path}: {e}")
        return None
