"""
Tool 6 — auth_register_and_login

Automatically register N test user accounts and log in.
Strategy hierarchy:
  1. Direct API registration (POST /api/Users or /api/register)
  2. GET /api/SecurityQuestions first (Juice Shop specific)
  3. Form-based registration via Playwright
  4. Known test credentials (admin@juice-sh.op/admin123, etc.)

Writes all sessions to state['sessions'].
"""

from __future__ import annotations

import re
import secrets
from typing import Any, Optional

import httpx
from loguru import logger

from cyberAI.llm.agent.state import RunState


# ---------------------------------------------------------------------------
# known credential combos to try for admin detection
# ---------------------------------------------------------------------------
_ADMIN_CREDS = [
    ("admin@juice-sh.op", "admin123"),
    ("admin@admin.com", "admin"),
    ("admin@example.com", "admin"),
    ("admin", "admin"),
    ("admin", "password"),
    ("admin", "admin123"),
    ("test@test.com", "test123"),
    ("user@example.com", "user123"),
]

_REGISTRATION_PATHS = [
    "/api/Users",
    "/api/register",
    "/auth/register",
    "/api/auth/register",
    "/users",
    "/register",
]

_LOGIN_PATHS = [
    "/rest/user/login",
    "/api/login",
    "/auth/login",
    "/api/auth/login",
    "/login",
    "/api/token",
]

_PII_FIELDS = {"email", "username", "name", "phone", "address", "role", "isAdmin"}


def _generate_email(role_label: str, run_id: str) -> str:
    token = secrets.token_hex(3)
    rid = run_id[:6] if run_id else "run"
    return f"cai_{role_label}_{rid}{token}@cyberhunt.local"


def _extract_jwt_from_response(resp: httpx.Response) -> Optional[str]:
    """Try to find JWT in response body or headers."""
    # Response body JSON patterns
    try:
        body = resp.json()
        # Juice Shop: {"authentication": {"token": "eyJ..."}}
        if isinstance(body, dict):
            for key in ("token", "jwt", "access_token", "accessToken", "id_token"):
                if key in body:
                    return str(body[key])
            auth = body.get("authentication") or body.get("auth") or body.get("data")
            if isinstance(auth, dict):
                for key in ("token", "jwt", "access_token", "accessToken"):
                    if key in auth:
                        return str(auth[key])
    except Exception:
        pass
    # Authorization header
    auth_header = resp.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    # Set-Cookie: token=...
    for cookie_header in resp.headers.get_list("set-cookie") if hasattr(resp.headers, "get_list") else []:
        m = re.search(r"(?:token|jwt|auth)=([A-Za-z0-9\._\-]+)", cookie_header, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _extract_user_id(resp_body: Any, email: str) -> Optional[Any]:
    """Try to extract user_id from registration/login response."""
    if isinstance(resp_body, dict):
        for key in ("id", "userId", "user_id", "uid"):
            if key in resp_body:
                return resp_body[key]
        data = resp_body.get("data") or resp_body.get("user") or resp_body.get("authentication")
        if isinstance(data, dict):
            for key in ("id", "userId", "user_id", "uid"):
                if key in data:
                    return data[key]
    return None


async def _try_login(client: httpx.AsyncClient, base_url: str, email: str, password: str) -> Optional[dict]:
    """Try all known login paths. Returns session dict or None."""
    for path in _LOGIN_PATHS:
        try:
            r = await client.post(
                path,
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code in (200, 201):
                jwt = _extract_jwt_from_response(r)
                if jwt:
                    user_id = _extract_user_id(r.json() if r.content else {}, email)
                    logger.debug(f"auth: login success via {path} for {email}")
                    return {
                        "email": email,
                        "password": password,
                        "jwt": jwt,
                        "user_id": user_id,
                        "role": "user",
                        "login_path": path,
                    }
        except Exception as e:
            logger.debug(f"auth: login attempt {path} failed: {e}")
    return None


async def _get_security_questions(client: httpx.AsyncClient) -> list[dict]:
    """Fetch Juice Shop security questions (required for registration)."""
    try:
        r = await client.get("/api/SecurityQuestions")
        if r.status_code == 200:
            body = r.json()
            data = body.get("data", body) if isinstance(body, dict) else body
            if isinstance(data, list) and data:
                return data
    except Exception:
        pass
    # Fallback: a generic question object that works for Juice Shop
    return [{"id": 1, "question": "Your eldest siblings middle name?", "createdAt": "2025-01-01", "updatedAt": "2025-01-01"}]


async def _api_register(
    client: httpx.AsyncClient,
    base_url: str,
    email: str,
    password: str,
) -> bool:
    """Attempt API-based registration. Returns True on success."""
    # First try Juice Shop format
    questions = await _get_security_questions(client)
    sq = questions[0] if questions else {"id": 1}

    # Juice Shop registration payload
    payload_juice = {
        "email": email,
        "password": password,
        "passwordRepeat": password,
        "securityQuestion": sq,
        "securityAnswer": "automated_test_answer",
    }

    for path in _REGISTRATION_PATHS:
        for payload in [payload_juice, {"email": email, "password": password}]:
            try:
                r = await client.post(path, json=payload, headers={"Content-Type": "application/json"})
                if r.status_code in (200, 201):
                    logger.info(f"auth: registered {email} via {path}")
                    return True
                if r.status_code == 409:
                    # Already exists — treat as success
                    logger.debug(f"auth: {email} already exists (409) at {path}")
                    return True
            except Exception as e:
                logger.debug(f"auth: register {path} failed: {e}")
    return False


async def _playwright_register(target_url: str, email: str, password: str) -> bool:
    """Form-based registration via Playwright. Returns True on success."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.debug("auth: playwright not available for form registration")
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context()
            page = await ctx.new_page()

            for path in ["/register", "/signup", "/#/register", "/auth/register", "/account/new"]:
                try:
                    await page.goto(target_url.rstrip("/") + path, wait_until="networkidle", timeout=10000)
                    pw_field = await page.query_selector('input[type="password"]')
                    if pw_field:
                        break
                except Exception:
                    continue

            # Fill email
            for sel in ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="email" i]']:
                f = await page.query_selector(sel)
                if f:
                    await f.fill(email)
                    break

            # Fill password fields
            for sel in ['input[type="password"]', 'input[name="password"]',
                        'input[name="passwordRepeat"]', 'input[name="confirm_password"]',
                        'input[name="password_confirmation"]']:
                f = await page.query_selector(sel)
                if f:
                    await f.fill(password)

            # Security question (Juice Shop specific)
            sq = await page.query_selector('select[aria-label*="question" i], mat-select')
            if sq:
                try:
                    await sq.select_option(index=0)
                    af = await page.query_selector('input[aria-label*="answer" i]')
                    if af:
                        await af.fill("automated_test_answer")
                except Exception:
                    pass

            # Submit
            for sel in ['button[type="submit"]', 'input[type="submit"]',
                        'button:has-text("Register")', 'button:has-text("Sign Up")',
                        'button:has-text("Create")', '[id*="register" i]']:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_load_state("networkidle", timeout=8000)
                    break

            await browser.close()
            logger.info(f"auth: playwright form registration attempted for {email}")
            return True
    except Exception as e:
        logger.debug(f"auth: playwright registration failed: {e}")
        return False


async def auth_register_and_login(
    target_url: str,
    num_users: int = 3,
    also_try_admin: bool = True,
    run_id: str = "",
    state: Optional[RunState] = None,
) -> dict:
    """
    Register N test users and log in to create the session pool.

    Returns:
    {
      "sessions_created": {
        "user_a": {"email": "...", "user_id": 3, "jwt": "eyJ...", "role": "user"},
        "user_b": {"email": "...", "user_id": 4, "jwt": "eyJ...", "role": "user"},
        "admin":  {"email": "admin@juice-sh.op", "user_id": 1, "jwt": "eyJ...", "role": "admin"}
      },
      "registration_method": "api",
      "errors": []
    }
    """
    base = target_url.rstrip("/")
    sessions: dict[str, dict] = {}
    errors: list[str] = []
    registration_method = "none"

    role_labels = ["a", "b", "c"][:num_users]

    async with httpx.AsyncClient(base_url=base, timeout=30.0, verify=False, follow_redirects=True) as client:
        for i, label in enumerate(role_labels):
            role_name = f"user_{label}"
            email = _generate_email(label, run_id)
            password = "CyberHunt@2026!"

            # Strategy 1: API registration
            ok = await _api_register(client, base, email, password)
            if ok:
                registration_method = "api"
            else:
                # Strategy 2: Playwright form
                ok = await _playwright_register(base, email, password)
                if ok:
                    registration_method = "form"

            if ok:
                session = await _try_login(client, base, email, password)
                if session:
                    session["role"] = "user"
                    sessions[role_name] = session
                    if state:
                        state.add_session(role_name, session)
                    logger.info(f"auth: session created for {role_name} ({email})")
                else:
                    errors.append(f"Registered {email} but login failed")
            else:
                errors.append(f"Registration failed for {role_name} ({email})")

        # Strategy: known admin credentials
        if also_try_admin:
            for admin_email, admin_password in _ADMIN_CREDS:
                session = await _try_login(client, base, admin_email, admin_password)
                if session:
                    session["role"] = "admin"
                    sessions["admin"] = session
                    if state:
                        state.add_session("admin", session)
                    logger.info(f"auth: admin session obtained ({admin_email})")
                    break
            else:
                logger.info("auth: no known admin credentials worked")

    return {
        "sessions_created": {
            name: {
                "email": s.get("email"),
                "user_id": s.get("user_id"),
                "jwt": (s.get("jwt") or "")[:30] + "...",
                "role": s.get("role", "user"),
            }
            for name, s in sessions.items()
        },
        "sessions_full": sessions,   # full JWTs for internal use
        "session_count": len(sessions),
        "registration_method": registration_method,
        "errors": errors,
    }
