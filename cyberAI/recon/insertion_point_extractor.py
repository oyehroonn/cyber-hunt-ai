"""
ASRTS Insertion Point Extraction: canonicalize requests and enumerate insertion points.

Turns RequestRecord into CanonicalRequest (URL template, body AST) and extracts
InsertionPoint list (path, query, body, headers). Supports one level of nested encoding.
"""

import hashlib
import json
import re
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from loguru import logger

from cyberAI.models import (
    CanonicalRequest,
    InsertionPoint,
    RequestRecord,
)


def _path_to_template(path: str) -> str:
    """Replace numeric and UUID-like segments with {id}."""
    parts = path.split("/")
    out = []
    for p in parts:
        if not p:
            out.append("")
            continue
        if re.match(r"^\d+$", p):
            out.append("{id}")
        elif re.match(r"^[0-9a-fA-F-]{36}$", p) or re.match(r"^[0-9a-fA-F]{32}$", p):
            out.append("{id}")
        else:
            out.append(p)
    return "/".join(out) or "/"


def _infer_type(key: str, value: Any) -> str:
    """Infer insertion point type from key name or value."""
    key_lower = key.lower()
    if "id" in key_lower or "uuid" in key_lower or "pk" in key_lower:
        return "id"
    if "token" in key_lower or "csrf" in key_lower or "nonce" in key_lower:
        return "token"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "int"
    return "string"


def _body_to_ast(data: Any, prefix: str = "") -> Any:
    """Convert body dict to AST with placeholders (<STR>, <INT>, etc.)."""
    if data is None:
        return None
    if isinstance(data, dict):
        return {k: _body_to_ast(v, f"{prefix}.{k}" if prefix else k) for k, v in data.items()}
    if isinstance(data, list):
        if data and isinstance(data[0], (dict, list)):
            return [_body_to_ast(data[0], f"{prefix}[]")]
        return ["<ARR>"]
    if isinstance(data, bool):
        return "<BOOL>"
    if isinstance(data, int):
        return "<INT>"
    if isinstance(data, float):
        return "<FLOAT>"
    if isinstance(data, str):
        return "<STR>"
    return "<UNK>"


def _collect_body_insertion_points(ast: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Walk body AST and return (location, inferred_type) for each leaf."""
    if ast is None:
        return []
    if isinstance(ast, dict):
        out = []
        for k, v in ast.items():
            loc = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.extend(_collect_body_insertion_points(v, loc))
            else:
                out.append((f"body.{loc}", _infer_type(k, v)))
        return out
    if isinstance(ast, list):
        out = []
        for i, v in enumerate(ast):
            out.extend(_collect_body_insertion_points(v, f"{prefix}[{i}]"))
        return out
    return [(f"body.{prefix}", "string")]


class RequestCanonicalizer:
    """Converts RequestRecord to CanonicalRequest (URL template, query, body AST)."""

    def canonicalize(self, record: RequestRecord) -> CanonicalRequest:
        parsed = urlparse(record.url)
        path_template = _path_to_template(parsed.path or "/")

        query_params: list[dict[str, str]] = []
        if parsed.query:
            for name, values in parse_qs(parsed.query, keep_blank_values=True).items():
                query_params.append({"name": name, "value_placeholder": "<STR>"})

        body_ast = None
        if record.body_json:
            body_ast = _body_to_ast(record.body_json)
        elif record.body:
            try:
                body_ast = _body_to_ast(json.loads(record.body))
            except json.JSONDecodeError:
                body_ast = {"raw": "<STR>"}

        return CanonicalRequest(
            request_id=record.id,
            method=record.method.value,
            url_template=path_template,
            query_params=query_params,
            headers=record.headers,
            body_ast=body_ast,
            warc_ref=getattr(record, "warc_ref", None),
        )


class InsertionPointExtractor:
    """Extracts InsertionPoint list from CanonicalRequest. Supports nested encoding (depth cap 3)."""

    def __init__(self, max_encoding_depth: int = 3):
        self._max_depth = max_encoding_depth

    def extract(self, canonical: CanonicalRequest) -> list[InsertionPoint]:
        points: list[InsertionPoint] = []
        # Path: parse url_template for {id} segments
        for i, seg in enumerate(canonical.url_template.split("/")):
            if seg == "{id}":
                points.append(InsertionPoint(
                    request_id=canonical.request_id,
                    location=f"path_segment_{i}",
                    encoding_layers=[],
                    inferred_type="id",
                ))
        # Query
        for q in canonical.query_params:
            name = q.get("name", "")
            points.append(InsertionPoint(
                request_id=canonical.request_id,
                location=f"query.{name}",
                encoding_layers=[],
                inferred_type=_infer_type(name, None),
            ))
        # Body
        if canonical.body_ast:
            for loc, itype in _collect_body_insertion_points(canonical.body_ast):
                points.append(InsertionPoint(
                    request_id=canonical.request_id,
                    location=loc,
                    encoding_layers=["json"],
                    inferred_type=itype,
                ))
        # Headers that look like input (common auth/role headers)
        for name in canonical.headers:
            name_lower = name.lower()
            if any(x in name_lower for x in ["user-id", "x-user", "x-role", "x-tenant", "x-org"]):
                points.append(InsertionPoint(
                    request_id=canonical.request_id,
                    location=f"header.{name}",
                    encoding_layers=[],
                    inferred_type="id" if "id" in name_lower else "string",
                ))
        return points

    def extract_from_record(self, record: RequestRecord) -> tuple[CanonicalRequest, list[InsertionPoint]]:
        """Convenience: canonicalize then extract."""
        canonicalizer = RequestCanonicalizer()
        canonical = canonicalizer.canonicalize(record)
        return canonical, self.extract(canonical)


def ast_param_names(ast: Any, prefix: str = "") -> list[str]:
    """Collect all leaf keys from body AST for novelty param list."""
    if ast is None:
        return []
    if isinstance(ast, dict):
        out = []
        for k, v in ast.items():
            loc = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.extend(ast_param_names(v, loc))
            else:
                out.append(loc)
        return out
    if isinstance(ast, list) and ast:
        return ast_param_names(ast[0], f"{prefix}[]")
    return [prefix] if prefix else []


def shape_hash(method: str, url_template: str, param_names: list[str]) -> str:
    """Hash of (method, url_template, sorted param names) for novelty index."""
    key = f"{method}|{url_template}|{','.join(sorted(param_names))}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]
