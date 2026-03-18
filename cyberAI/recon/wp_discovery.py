"""
WordPress/WooCommerce Deep Discovery (optional enrichment).

Goal:
- Extract additional crawl targets from sitemap.xml and robots.txt
  and enumerate public wp-json routes to expand recon coverage.

This is intentionally non-destructive and does not attempt to bypass bot
protections or authentication barriers.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urljoin

from loguru import logger

from cyberAI.config import get_config
from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json, generate_run_id
from cyberAI.utils.http_client import AsyncHTTPClient


def _parse_sitemap_xml(xml_text: str, max_urls: int = 500) -> list[str]:
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return urls

    # Support both sitemapindex and urlset
    ns = ""
    if root.tag.startswith("{") and "}" in root.tag:
        ns = root.tag.split("}", 1)[0] + "}"

    if root.tag.endswith("sitemapindex"):
        for sm in root.findall(f"{ns}sitemap"):
            loc = sm.find(f"{ns}loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
                if len(urls) >= max_urls:
                    break
        return urls

    if root.tag.endswith("urlset"):
        for u in root.findall(f"{ns}url"):
            loc = u.find(f"{ns}loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
                if len(urls) >= max_urls:
                    break
        return urls

    return urls


async def run_wp_discovery(
    base_url: str,
    run_id: Optional[str] = None,
    max_sitemap_urls: int = 500,
) -> dict:
    """
    Best-effort WordPress/WooCommerce discovery.

    Outputs:
    - recon/intelligence/wp_discovery.json
    - recon/intelligence/wp_routes.json  (hidden_routes-compatible list)
    """
    config = get_config()
    rid = run_id or generate_run_id()
    client = AsyncHTTPClient(base_url=base_url)

    robots_text: Optional[str] = None
    sitemap_urls: list[str] = []
    sitemap_targets: list[str] = []
    wpjson_index: Optional[dict] = None
    wpjson_routes: list[str] = []

    try:
        # robots.txt (may contain Sitemap directives)
        try:
            resp, rec = await client.get("/robots.txt", record=True, follow_redirects=False)
            if resp.status_code == 200 and rec and rec.response_body:
                robots_text = rec.response_body
        except Exception as e:
            logger.debug(f"robots.txt fetch failed: {e}")

        # default sitemap location
        for candidate in ["/sitemap.xml", "/sitemap_index.xml"]:
            try:
                resp, rec = await client.get(candidate, record=True, follow_redirects=False)
                if resp.status_code == 200 and rec and rec.response_body:
                    sitemap_urls = _parse_sitemap_xml(rec.response_body, max_urls=max_sitemap_urls)
                    if sitemap_urls:
                        break
            except Exception as e:
                logger.debug(f"sitemap fetch failed ({candidate}): {e}")

        # If we got a sitemap index, fetch a few nested sitemaps and collect URL targets
        if sitemap_urls and any(u.endswith(".xml") for u in sitemap_urls[:10]):
            for sm_url in sitemap_urls[:20]:
                try:
                    resp, rec = await client.get(sm_url, record=True, follow_redirects=False)
                    if resp.status_code == 200 and rec and rec.response_body:
                        sitemap_targets.extend(_parse_sitemap_xml(rec.response_body, max_urls=max_sitemap_urls))
                except Exception:
                    continue
            sitemap_targets = sitemap_targets[:max_sitemap_urls]
        else:
            sitemap_targets = sitemap_urls[:max_sitemap_urls]

        # wp-json index (public routes enumeration)
        try:
            resp, rec = await client.get("/wp-json/", record=True, follow_redirects=False)
            if resp.status_code == 200 and rec and isinstance(rec.response_json, dict):
                wpjson_index = rec.response_json
                # WordPress index includes "routes" key in many setups; otherwise namespaces can guide.
                routes = wpjson_index.get("routes")
                if isinstance(routes, dict):
                    wpjson_routes = sorted(list(routes.keys()))[:2000]
        except Exception as e:
            logger.debug(f"wp-json fetch failed: {e}")

    finally:
        await client.close()

    out_path = config.get_output_path("recon", "intelligence", "wp_discovery.json")
    data = add_meta_to_output(
        {
            "robots_txt_present": bool(robots_text),
            "sitemap_targets": sitemap_targets,
            "wpjson_routes": wpjson_routes,
        },
        target_url=config.target_url,
        phase="recon",
        run_id=rid,
    )
    atomic_write_json(out_path, data)

    wp_routes_path = config.get_output_path("recon", "intelligence", "wp_routes.json")
    hidden_routes = [{"path": u, "source": "sitemap"} for u in sitemap_targets]
    atomic_write_json(
        wp_routes_path,
        add_meta_to_output({"hidden_routes": hidden_routes}, target_url=config.target_url, phase="recon", run_id=rid),
    )

    logger.info(f"WP discovery saved: {len(sitemap_targets)} sitemap URLs, {len(wpjson_routes)} wp-json routes")
    return {
        "sitemap_urls": len(sitemap_targets),
        "wpjson_routes": len(wpjson_routes),
        "sitemap_targets": sitemap_targets,
    }

