"""Step 20.4: Evidence Pack. Resolves WARC refs and includes request/response content."""
from pathlib import Path
from typing import Optional, Union

from cyberAI.models import Finding, VerifiedFinding

try:
    from cyberAI.storage.warc_writer import read_warc_ref
except ImportError:
    read_warc_ref = None


def generate_evidence_pack(
    finding: Union[Finding, VerifiedFinding],
    output_dir: Optional[Union[Path, str]] = None,
) -> dict:
    """
    Build evidence pack for a finding. If output_dir is set, resolve each evidence_warc_ref
    by reading from WARC and include http_headers + body_preview per ref.
    """
    refs = getattr(finding, "evidence_warc_refs", []) or []
    pack = {
        "screenshots": [],
        "requests": getattr(finding, "request_proof", None),
        "state_diff": {"before": getattr(finding, "before_state", None), "after": getattr(finding, "after_state", None)},
        "evidence_warc_refs": refs,
    }
    if output_dir and refs and read_warc_ref is not None:
        out = Path(output_dir)
        pack["warc_records"] = []
        for ref in refs:
            record = read_warc_ref(ref, out)
            if record:
                pack["warc_records"].append(record)
    return pack
