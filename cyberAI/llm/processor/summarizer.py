"""
Report Summarizer

LLM-powered structured summarization of security vulnerability reports.
"""

import json
import time
import re
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


class StructuredReport(BaseModel):
    """Structured summary of a vulnerability report."""
    title: str = Field(default="Unknown Vulnerability", description="Short descriptive title")
    vuln_class: str = Field(default="Other", description="Vulnerability classification")
    cwe: Optional[str] = Field(default=None, description="CWE identifier if known")
    cvss_score: Optional[float] = Field(default=None, description="CVSS score")
    severity: str = Field(default="medium", description="Severity level")
    affected_component: Optional[str] = Field(default=None, description="Affected system component")
    attack_vector: str = Field(default="Vulnerability details not available", description="Step-by-step attack description")
    root_cause: str = Field(default="Security control failure", description="Underlying code/design failure")
    impact: str = Field(default="Security impact", description="What an attacker can achieve")
    remediation: str = Field(default="Implement proper security controls", description="How to fix the vulnerability")
    test_hints: list[str] = Field(default_factory=list, description="Testing indicators")
    keywords: list[str] = Field(default_factory=list, description="Technical terms")
    
    # Metadata
    source: str = Field(default="unknown")
    original_id: str = Field(default="")
    original_url: Optional[str] = Field(default=None)
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


SUMMARIZATION_PROMPT = """Analyze this security vulnerability report and extract a structured summary.

REPORT CONTENT:
{report_content}

METADATA:
- Source: {source}
- Original Severity: {severity}
- Original Vuln Type: {vuln_type}
- CWE: {cwe}

Extract a structured JSON with these exact fields:
{{
  "title": "short descriptive title (max 80 chars)",
  "vuln_class": "one of: IDOR | Auth Bypass | Race Condition | XSS | SSRF | SQL Injection | Business Logic | Command Injection | Path Traversal | XXE | CSRF | Insecure Deserialization | Information Disclosure | Privilege Escalation | Open Redirect | JWT Vulnerabilities | API Security | Other",
  "cwe": "CWE-XXX if known, or null",
  "cvss_score": number between 0-10 or null,
  "severity": "critical | high | medium | low | informational",
  "affected_component": "which part of the system was vulnerable",
  "attack_vector": "step by step how the attack works, in plain language",
  "root_cause": "what code/design failure caused this vulnerability",
  "impact": "what an attacker can achieve by exploiting this",
  "remediation": "how to fix this vulnerability",
  "test_hints": ["list of things to look for when testing for this class of bug"],
  "keywords": ["relevant technical terms for search/retrieval"]
}}

IMPORTANT:
- Be specific and actionable in attack_vector and test_hints
- Focus on the technical details that would help identify similar vulnerabilities
- If information is missing, make reasonable inferences based on the vuln_class
- test_hints should be specific indicators a security tester would look for
- Output ONLY valid JSON, no additional text

JSON:"""


class ReportSummarizer:
    """Summarizes raw vulnerability reports into structured format using LLM."""
    
    def __init__(self, data_dir: Path, llm_client: Optional[Any] = None):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = llm_client
        
    def _load_raw_report(self, filepath: Path) -> Optional[dict]:
        """Load a raw report from JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[dim]Error loading {filepath}: {e}[/dim]")
            return None
    
    def _save_processed_report(self, report: StructuredReport, source: str, report_id: str) -> Path:
        """Save processed report to disk."""
        filename = f"{source}_{report_id}.json"
        filepath = self.processed_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _is_processed(self, source: str, report_id: str) -> bool:
        """Check if report has already been processed."""
        filename = f"{source}_{report_id}.json"
        return (self.processed_dir / filename).exists()
    
    def _extract_text_content(self, raw: dict) -> str:
        """Extract main text content from raw report."""
        parts = []
        
        if raw.get("title"):
            parts.append(f"Title: {raw['title']}")
        
        if raw.get("description"):
            parts.append(f"Description: {raw['description']}")
        
        if raw.get("body"):
            body = raw["body"]
            # Truncate very long bodies
            if len(body) > 8000:
                body = body[:8000] + "...[truncated]"
            parts.append(f"Full Content:\n{body}")
        
        # Include metadata if available
        metadata = raw.get("metadata", {})
        if metadata.get("attack_vector"):
            parts.append(f"Attack Vector: {metadata['attack_vector']}")
        if metadata.get("solution"):
            parts.append(f"Solution: {metadata['solution']}")
        if metadata.get("remediation"):
            parts.append(f"Remediation: {metadata['remediation']}")
        
        return "\n\n".join(parts)
    
    def _call_llm(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call LLM with retry logic."""
        if not self.llm_client:
            return None
        
        for attempt in range(max_retries):
            try:
                response = self.llm_client.generate(prompt)
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    console.print(f"[yellow]LLM error, retrying in {wait}s: {e}[/yellow]")
                    time.sleep(wait)
                else:
                    console.print(f"[red]LLM failed after {max_retries} attempts: {e}[/red]")
        return None
    
    def _parse_llm_response(self, response: str) -> Optional[dict]:
        """Parse JSON from LLM response."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return None
        except json.JSONDecodeError as e:
            console.print(f"[dim]JSON parse error: {e}[/dim]")
            return None
    
    def _fallback_summarize(self, raw: dict) -> dict:
        """Generate summary without LLM using heuristics."""
        
        # Helper to safely get string value
        def safe_str(val, default: str = "") -> str:
            if val is None:
                return default
            if isinstance(val, str):
                return val if val.strip() else default
            try:
                return str(val)
            except Exception:
                return default
        
        # Safely extract text content
        try:
            text = self._extract_text_content(raw).lower()
        except Exception:
            text = ""
        
        # Detect vulnerability class from text patterns
        vuln_patterns = [
            (r"idor|insecure direct object", "IDOR"),
            (r"sql.?inject", "SQL Injection"),
            (r"xss|cross.?site.?script", "XSS"),
            (r"ssrf|server.?side.?request", "SSRF"),
            (r"csrf|cross.?site.?request.?forg", "CSRF"),
            (r"xxe|xml.?external", "XXE"),
            (r"auth.?bypass|broken.?auth", "Auth Bypass"),
            (r"race.?condition", "Race Condition"),
            (r"business.?logic", "Business Logic"),
            (r"command.?inject|rce", "Command Injection"),
            (r"path.?traversal|directory.?traversal", "Path Traversal"),
            (r"deserializ", "Insecure Deserialization"),
            (r"privilege.?escalat", "Privilege Escalation"),
            (r"information.?disclos|info.?leak", "Information Disclosure"),
            (r"open.?redirect", "Open Redirect"),
            (r"jwt|json.?web.?token", "JWT Vulnerabilities"),
            (r"api.?security", "API Security"),
        ]
        
        vuln_class = "Other"
        for pattern, vclass in vuln_patterns:
            try:
                if re.search(pattern, text):
                    vuln_class = vclass
                    break
            except Exception:
                continue
        
        # Generate test hints based on vuln class
        test_hints_map = {
            "IDOR": ["Test changing object IDs in requests", "Check if user A can access user B's resources", "Enumerate sequential IDs"],
            "SQL Injection": ["Test single quotes in inputs", "Check for error messages", "Try UNION-based injection"],
            "XSS": ["Inject script tags", "Test event handlers", "Check for reflected inputs"],
            "SSRF": ["Test internal IP addresses", "Check URL parameters", "Try cloud metadata endpoints"],
            "Auth Bypass": ["Test direct URL access", "Check session handling", "Try manipulating auth tokens"],
            "Race Condition": ["Send concurrent requests", "Test coupon/discount codes", "Check atomic operations"],
            "Business Logic": ["Test workflow sequences", "Check boundary conditions", "Verify state transitions"],
        }
        
        # Build attack_vector from description or body, ensuring it's never None/empty
        desc = raw.get("description") if isinstance(raw, dict) else None
        body = raw.get("body") if isinstance(raw, dict) else None
        
        attack_vector = ""
        if desc and isinstance(desc, str) and desc.strip():
            attack_vector = desc.strip()[:500]
        elif body and isinstance(body, str) and body.strip():
            attack_vector = body.strip()[:500]
        
        if not attack_vector:
            attack_vector = f"Potential {vuln_class} vulnerability identified in the target system"
        
        # Build title safely
        title = safe_str(raw.get("title") if isinstance(raw, dict) else None, "")
        if not title:
            title = f"Unknown {vuln_class} Vulnerability"
        
        # Build severity safely
        severity = safe_str(raw.get("severity") if isinstance(raw, dict) else None, "").lower()
        if severity not in ["critical", "high", "medium", "low", "informational"]:
            severity = "medium"
        
        # Build source safely
        source = safe_str(raw.get("source") if isinstance(raw, dict) else None, "unknown")
        
        return {
            "title": title,
            "vuln_class": vuln_class,
            "cwe": raw.get("cwe") if isinstance(raw, dict) else None,
            "cvss_score": raw.get("cvss_score") if isinstance(raw, dict) else None,
            "severity": severity,
            "affected_component": raw.get("affected_component") if isinstance(raw, dict) else None,
            "attack_vector": attack_vector,
            "root_cause": f"Insufficient {vuln_class.lower()} protection",
            "impact": f"Attacker could exploit {vuln_class.lower()} vulnerability",
            "remediation": f"Implement proper {vuln_class.lower()} controls",
            "test_hints": test_hints_map.get(vuln_class, ["Test for common vulnerability patterns"]),
            "keywords": [vuln_class.lower(), source],
        }
    
    def summarize_report(self, raw: dict, use_llm: bool = True) -> Optional[StructuredReport]:
        """
        Summarize a raw report into structured format.
        
        Args:
            raw: Raw report dictionary
            use_llm: Whether to use LLM for summarization
            
        Returns:
            Structured report or None if failed
        """
        source = raw.get("source", "unknown")
        report_id = raw.get("id", "unknown")
        
        if use_llm and self.llm_client:
            # Build prompt
            content = self._extract_text_content(raw)
            prompt = SUMMARIZATION_PROMPT.format(
                report_content=content,
                source=source,
                severity=raw.get("severity", "unknown"),
                vuln_type=raw.get("vuln_type", "unknown"),
                cwe=raw.get("cwe", "unknown"),
            )
            
            # Call LLM
            response = self._call_llm(prompt)
            if response:
                parsed = self._parse_llm_response(response)
                if parsed:
                    # Merge with original metadata
                    parsed["source"] = source
                    parsed["original_id"] = report_id
                    parsed["original_url"] = raw.get("url")
                    
                    try:
                        return StructuredReport(**parsed)
                    except Exception as e:
                        console.print(f"[dim]Validation error, using fallback: {e}[/dim]")
        
        # Fallback to heuristic summarization
        try:
            fallback_data = self._fallback_summarize(raw)
            fallback_data["source"] = source
            fallback_data["original_id"] = report_id
            fallback_data["original_url"] = raw.get("url")
            
            return StructuredReport(**fallback_data)
        except Exception as e:
            console.print(f"[red]Failed to process report {report_id}: {e}[/red]")
            return None
    
    def process_all(self, use_llm: bool = True, progress: Optional[Progress] = None,
                    task: Optional[TaskID] = None) -> list[StructuredReport]:
        """
        Process all raw reports in the data directory.
        
        Args:
            use_llm: Whether to use LLM for summarization
            progress: Rich progress bar
            task: Task ID for progress tracking
            
        Returns:
            List of processed reports
        """
        processed = []
        raw_files = list(self.raw_dir.glob("*.json"))
        
        console.print(f"[cyan]Processing {len(raw_files)} raw reports...[/cyan]")
        
        for filepath in raw_files:
            # Extract source and ID from filename
            filename = filepath.stem
            parts = filename.split("_", 1)
            source = parts[0] if parts else "unknown"
            report_id = parts[1] if len(parts) > 1 else filename
            
            # Skip if already processed
            if self._is_processed(source, report_id):
                if progress and task:
                    progress.update(task, advance=1)
                continue
            
            # Load raw report
            raw = self._load_raw_report(filepath)
            if not raw:
                continue
            
            # Summarize
            report = self.summarize_report(raw, use_llm=use_llm)
            if report:
                self._save_processed_report(report, source, report_id)
                processed.append(report)
            
            if progress and task:
                progress.update(task, advance=1)
        
        console.print(f"[green]Processed {len(processed)} new reports[/green]")
        return processed
    
    def get_processed_count(self) -> int:
        """Get count of processed reports."""
        return len(list(self.processed_dir.glob("*.json")))
    
    def load_all_processed(self) -> list[StructuredReport]:
        """Load all processed reports from disk."""
        reports = []
        for filepath in self.processed_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    reports.append(StructuredReport(**data))
            except Exception as e:
                console.print(f"[dim]Error loading {filepath}: {e}[/dim]")
        return reports


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    summarizer = ReportSummarizer(data_dir)
    
    # Process without LLM (fallback mode)
    processed = summarizer.process_all(use_llm=False)
    print(f"Processed {len(processed)} reports")
