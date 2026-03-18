"""
ASRTS §4.1: Knowledge graph builder (file-based, no Neo4j).
Consumes endpoints, insertion points, roles, findings; writes nodes.json and edges.json
for querying with pandas or simple scripts (1-2 hop analysis).
"""

import hashlib
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from cyberAI.config import get_config
from cyberAI.utils.helpers import add_meta_to_output, atomic_write_json, load_json


def _node_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:12]
    return f"{prefix}_{h}"


def build_graph_from_recon(
    run_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
    endpoints_path: Optional[Path] = None,
    insertion_points_path: Optional[Path] = None,
    findings_glob: Optional[str] = None,
) -> tuple[list[dict], list[dict]]:
    """
    Load recon/test outputs and build nodes + edges (file-based graph).
    Returns (nodes_list, edges_list); also writes to recon/intelligence/knowledge_graph/.
    """
    config = get_config()
    run_id = run_id or getattr(config, "run_id", "") or ""
    out = output_dir or config.output_dir
    base = out / "recon" / "intelligence" / "knowledge_graph"
    base.mkdir(parents=True, exist_ok=True)

    nodes: list[dict] = []
    edges: list[dict] = []
    endpoint_ids: dict[str, str] = {}  # key -> node id

    # Endpoints (from network intel or API spec)
    ep_path = endpoints_path or config.get_output_path("recon", "intelligence", "endpoints.json")
    if not ep_path.exists():
        ep_path = config.get_output_path("recon", "intelligence", "api_spec_endpoints.json")
    if ep_path.exists():
        data = load_json(ep_path)
        eps = (data or {}).get("endpoints") or []
        for e in eps:
            method = e.get("method", "GET")
            url = e.get("url", "") or e.get("path_pattern", "")
            key = f"{method}:{url}"
            nid = _node_id("ep", key)
            endpoint_ids[key] = nid
            nodes.append({"id": nid, "label": "Endpoint", "method": method, "url": url, "path_pattern": e.get("path_pattern")})
            for role, allowed in (e.get("role_access") or {}).items():
                rid = _node_id("role", role)
                if not any(n["id"] == rid for n in nodes):
                    nodes.append({"id": rid, "label": "Role", "name": role})
                edges.append({"from": nid, "to": rid, "type": "REQUIRES_AUTH", "allowed": allowed})

    # Insertion points -> Parameter nodes, EXPOSES edges
    ip_path = insertion_points_path or config.get_output_path("recon", "intelligence", "insertion_points.json")
    if ip_path.exists():
        data = load_json(ip_path)
        ips = (data or {}).get("insertion_points") or []
        for ip in ips:
            loc = ip.get("location", "")
            req_id = ip.get("request_id", "")
            pid = _node_id("param", req_id, loc)
            if not any(n["id"] == pid for n in nodes):
                nodes.append({"id": pid, "label": "Parameter", "name": loc, "inferred_type": ip.get("inferred_type", "string")})
            for key, eid in endpoint_ids.items():
                if req_id in key or key.endswith(loc.split(".")[0] if "." in loc else ""):
                    edges.append({"from": eid, "to": pid, "type": "EXPOSES"})
                    break
            else:
                ep_key = next((k for k in endpoint_ids), None)
                if ep_key:
                    edges.append({"from": endpoint_ids[ep_key], "to": pid, "type": "EXPOSES"})

    # Findings -> EVIDENCE_IN -> WARCRef
    findings_dir = out / "testing" / "findings"
    if findings_dir.exists():
        for path in findings_dir.glob(findings_glob or "*.json"):
            data = load_json(path)
            findings_list = (data or {}).get("findings") or []
            for f in findings_list:
                fid = f.get("id") or _node_id("f", f.get("title", ""), f.get("asset", ""))
                if not any(n["id"] == fid for n in nodes):
                    nodes.append({"id": fid, "label": "Finding", "title": f.get("title"), "severity": f.get("severity"), "asset": f.get("asset")})
                for warc_ref in f.get("evidence_warc_refs") or []:
                    wid = _node_id("warc", warc_ref)
                    if not any(n["id"] == wid for n in nodes):
                        nodes.append({"id": wid, "label": "WARCRef", "path": warc_ref})
                    edges.append({"from": fid, "to": wid, "type": "EVIDENCE_IN"})

    atomic_write_json(base / "nodes.json", add_meta_to_output({"nodes": nodes}, target_url="", phase="recon", run_id=run_id))
    atomic_write_json(base / "edges.json", add_meta_to_output({"edges": edges}, target_url="", phase="recon", run_id=run_id))
    logger.info(f"Knowledge graph: {len(nodes)} nodes, {len(edges)} edges")
    return nodes, edges


def run_graph_builder(run_id: Optional[str] = None) -> tuple[list[dict], list[dict]]:
    """Convenience: build graph from default paths."""
    return build_graph_from_recon(run_id=run_id)
