"""
Optional automated registration of test accounts from AUTO_REGISTER_SPEC (any target).
Fills config.role_accounts when empty so recon can run ensure_sessions_for_roles.
"""

from __future__ import annotations

import json
import re
import secrets
from typing import Any, Optional

import httpx
from loguru import logger

from cyberAI.config import Config, RoleAccount, get_config


def _template_fill(template: Any, mapping: dict[str, str]) -> Any:
    if isinstance(template, str):
        out = template
        for k, v in mapping.items():
            out = out.replace("{" + k + "}", v)
        return out
    if isinstance(template, dict):
        return {kk: _template_fill(vv, mapping) for kk, vv in template.items()}
    if isinstance(template, list):
        return [_template_fill(x, mapping) for x in template]
    return template


async def ensure_auto_registered_roles(config: Optional[Config] = None, run_id: str = "") -> int:
    """
    If AUTO_REGISTER_SPEC is set and fewer than two roles exist, register users via HTTP
    and append RoleAccount entries. Returns number of new roles added.
    """
    config = config or get_config()
    spec_raw = (config.auto_register_spec or "").strip()
    if not spec_raw:
        return 0
    if len(config.role_accounts) >= 2:
        logger.debug("auto_register: role_accounts already populated; skip")
        return 0

    try:
        spec = json.loads(spec_raw)
    except json.JSONDecodeError as e:
        logger.warning(f"auto_register: invalid AUTO_REGISTER_SPEC JSON: {e}")
        return 0

    base = (config.target_url or "").rstrip("/")
    if not base:
        logger.warning("auto_register: TARGET_URL missing")
        return 0

    path = spec.get("path") or spec.get("url") or "/"
    if path.startswith("http"):
        from urllib.parse import urlparse

        u = urlparse(path)
        register_url = path
    else:
        register_url = base + (path if path.startswith("/") else "/" + path)

    method = (spec.get("method") or "POST").upper()
    headers = spec.get("headers") or {"Content-Type": "application/json"}
    body_template = spec.get("body") or {}
    roles_spec = spec.get("roles") or [
        {"role": "user_high", "email_prefix": "cyberai_a"},
        {"role": "user_low", "email_prefix": "cyberai_b"},
    ]

    added = 0
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        for rs in roles_spec[:2]:
            role = rs.get("role") or "user"
            prefix = rs.get("email_prefix") or f"cy_{role}"
            email = f"{prefix}_{secrets.token_hex(4)}@test.invalid"
            password = rs.get("password") or secrets.token_urlsafe(14)
            mapping = {
                "email": email,
                "password": password,
                "run_id": run_id or "run",
            }
            body = _template_fill(body_template, mapping)
            try:
                if method == "POST":
                    r = await client.post(register_url, headers=headers, json=body)
                elif method == "PUT":
                    r = await client.put(register_url, headers=headers, json=body)
                else:
                    r = await client.request(method, register_url, headers=headers, json=body)
                ok = r.status_code in (200, 201, 204)
                if not ok:
                    logger.warning(
                        f"auto_register: registration HTTP {r.status_code} for {role}: {r.text[:200]}"
                    )
                if ok:
                    config.role_accounts.append(
                        RoleAccount(role=role, username=email, password=password)
                    )
                    added += 1
                    logger.info(f"auto_register: registered role {role} ({email})")
            except Exception as e:
                logger.debug(f"auto_register: {e}")

    if added:
        cred_path = config.get_output_path("sessions", f"auto_registered_{run_id}.json")
        cred_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cred_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"role": a.role, "username": a.username} for a in config.role_accounts[-added:]],
                f,
                indent=2,
            )

    return added
