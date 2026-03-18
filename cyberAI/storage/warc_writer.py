"""
WARC (Web ARChive, ISO 28500) writer for evidence-grade request/response capture.

Each write_record() appends a request record and a response record; returns a ref
of the form {run_id}/{filename}#{offset}_{length} for the response record (evidence).
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

from loguru import logger


def _warc_header(
    record_type: str,
    target_uri: str,
    content_length: int,
    record_id: Optional[str] = None,
    content_type: Optional[str] = None,
) -> str:
    """Build WARC 1.1 record header lines."""
    rid = record_id or f"<urn:uuid:{uuid4()}>"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"WARC/1.1",
        f"WARC-Type: {record_type}",
        f"WARC-Record-ID: {rid}",
        f"WARC-Date: {date}",
        f"WARC-Target-URI: {target_uri}",
        f"Content-Length: {content_length}",
    ]
    if content_type:
        lines.append(f"Content-Type: {content_type}")
    lines.append("")
    return "\r\n".join(lines) + "\r\n"


def _serialize_request(method: str, url: str, headers: dict, body: Optional[bytes]) -> bytes:
    """HTTP request line + headers + body for WARC request block."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    line = f"{method} {path} HTTP/1.1\r\n"
    head = "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n"
    body = body or b""
    return line.encode("utf-8", errors="replace") + head.encode("utf-8", errors="replace") + body


def _serialize_response(status: int, headers: dict, body: Optional[bytes]) -> bytes:
    """HTTP response line + headers + body for WARC response block."""
    line = f"HTTP/1.1 {status} OK\r\n" if status >= 200 else f"HTTP/1.1 {status}\r\n"
    head = "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n"
    body = body or b""
    return line.encode("utf-8", errors="replace") + head.encode("utf-8", errors="replace") + body


class WARCWriter:
    """
    Appends WARC records to a file under output_dir/warc/{run_id}/.
    Returns a ref string: warc://{run_id}/{basename}#{offset}_{length}
    """

    def __init__(self, output_dir: Path, run_id: str, enabled: bool = True):
        self.output_dir = Path(output_dir)
        self.run_id = run_id
        self.enabled = enabled
        self._warc_dir = self.output_dir / "warc" / run_id
        self._current_path: Optional[Path] = None
        self._current_file = None
        self._bytes_written = 0

    def _ensure_file(self) -> Path:
        """Open a new WARC file if needed (one per run or rotate by size later)."""
        if self._current_file is not None and self._current_file.writable():
            return self._current_path
        self._warc_dir.mkdir(parents=True, exist_ok=True)
        name = f"capture_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.warc"
        self._current_path = self._warc_dir / name
        self._current_file = open(self._current_path, "ab")
        return self._current_path

    def write_record(
        self,
        method: str,
        url: str,
        request_headers: dict[str, str],
        request_body: Optional[bytes],
        response_status: int,
        response_headers: dict[str, str],
        response_body: Optional[bytes],
    ) -> Optional[str]:
        """
        Append one request + one response WARC record. Return ref for the response record.

        Ref format: warc://{run_id}/{filename}#{offset}_{length}
        """
        if not self.enabled:
            return None

        try:
            path = self._ensure_file()
            f = self._current_file
            assert f is not None

            req_block = _serialize_request(method, url, request_headers, request_body)
            resp_block = _serialize_response(response_status, response_headers, response_body)

            # Request record
            req_header = _warc_header("request", url, len(req_block))
            req_bytes = req_header.encode("utf-8") + req_block
            f.write(req_bytes)
            f.write(b"\r\n\r\n")

            # Response record (this is the one we reference as evidence)
            resp_header = _warc_header(
                "response",
                url,
                len(resp_block),
                content_type=response_headers.get("Content-Type", response_headers.get("content-type")),
            )
            start = f.tell()
            resp_header_b = resp_header.encode("utf-8")
            f.write(resp_header_b)
            f.write(resp_block)
            f.write(b"\r\n\r\n")
            length = len(resp_header_b) + len(resp_block)

            ref = f"warc://{self.run_id}/{path.name}#{start}_{length}"
            return ref
        except Exception as e:
            logger.warning(f"WARC write failed: {e}")
            return None

    def close(self) -> None:
        """Close the current WARC file."""
        if self._current_file:
            try:
                self._current_file.close()
            except Exception:
                pass
            self._current_file = None
        self._current_path = None

    def __enter__(self) -> "WARCWriter":
        return self

    def __exit__(self, *args) -> None:
        self.close()


def read_warc_ref(ref: str, output_dir: Path) -> Optional[dict]:
    """
    Read a WARC record by ref (warc://{run_id}/{filename}#{offset}_{length}).
    Returns dict with warc_header, http_payload (response or request), and body_preview (first 2KB).
    """
    if not ref or not ref.startswith("warc://"):
        return None
    try:
        rest = ref[7:]  # after warc://
        part, offset_len = rest.rsplit("#", 1)
        run_id, filename = part.split("/", 1)
        offset_str, length_str = offset_len.split("_")
        offset, length = int(offset_str), int(length_str)
        warc_path = Path(output_dir) / "warc" / run_id / filename
        if not warc_path.is_file():
            return None
        with open(warc_path, "rb") as f:
            f.seek(offset)
            block = f.read(length)
        if not block:
            return None
        # Block is WARC header + CRLFCRLF + payload (HTTP response or request)
        idx = block.find(b"\r\n\r\n")
        if idx == -1:
            return {"raw_preview": block[:2048].decode("utf-8", errors="replace")}
        warc_header = block[:idx].decode("utf-8", errors="replace")
        payload = block[idx + 4:]
        # Payload is HTTP status line + headers + body
        idx2 = payload.find(b"\r\n\r\n")
        if idx2 == -1:
            body = payload
            headers_section = payload[:500].decode("utf-8", errors="replace")
        else:
            headers_section = payload[:idx2].decode("utf-8", errors="replace")
            body = payload[idx2 + 4:]
        body_preview = body[:2048].decode("utf-8", errors="replace") if len(body) < 100_000 else "(truncated)"
        return {
            "warc_ref": ref,
            "warc_header": warc_header[:500],
            "http_headers": headers_section,
            "body_preview": body_preview,
            "body_size": len(body),
        }
    except Exception as e:
        logger.debug(f"read_warc_ref {ref}: {e}")
        return None
