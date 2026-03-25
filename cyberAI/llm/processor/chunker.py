"""
Report Chunker

Smart semantic chunking of processed reports for optimal embedding and retrieval.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from rich.console import Console

console = Console()


@dataclass
class ReportChunk:
    """A semantically coherent chunk of a security report."""
    id: str
    report_id: str
    source: str
    chunk_type: str  # "attack_pattern", "test_hints", "remediation", "full"
    content: str
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "report_id": self.report_id,
            "source": self.source,
            "chunk_type": self.chunk_type,
            "content": self.content,
            "metadata": self.metadata,
        }


class ReportChunker:
    """Chunks processed security reports for embedding."""
    
    # Chunk type definitions
    CHUNK_TYPES = {
        "attack_pattern": {
            "fields": ["vuln_class", "attack_vector"],
            "template": "Vulnerability Type: {vuln_class}\n\nAttack Vector:\n{attack_vector}",
            "description": "How the vulnerability is exploited",
        },
        "test_hints": {
            "fields": ["vuln_class", "root_cause", "test_hints"],
            "template": "Vulnerability: {vuln_class}\n\nRoot Cause: {root_cause}\n\nTesting Indicators:\n{test_hints_str}",
            "description": "What to look for when testing",
        },
        "remediation": {
            "fields": ["vuln_class", "impact", "remediation"],
            "template": "Vulnerability: {vuln_class}\n\nImpact: {impact}\n\nRemediation:\n{remediation}",
            "description": "How to fix and why it matters",
        },
        "full_context": {
            "fields": ["title", "vuln_class", "attack_vector", "root_cause", "impact", "remediation"],
            "template": "Title: {title}\n\nVulnerability Class: {vuln_class}\n\nAttack Vector:\n{attack_vector}\n\nRoot Cause: {root_cause}\n\nImpact: {impact}\n\nRemediation:\n{remediation}",
            "description": "Complete vulnerability context",
        },
    }
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
    
    def _generate_chunk_id(self, report_id: str, chunk_type: str) -> str:
        """Generate unique chunk ID."""
        content = f"{report_id}_{chunk_type}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _load_processed_report(self, filepath: Path) -> Optional[dict]:
        """Load a processed report from JSON."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[dim]Error loading {filepath}: {e}[/dim]")
            return None
    
    def chunk_report(self, report: dict, include_full: bool = True) -> list[ReportChunk]:
        """
        Chunk a single processed report into semantic segments.
        
        Args:
            report: Processed report dictionary
            include_full: Whether to include full_context chunk
            
        Returns:
            List of chunks
        """
        chunks = []
        report_id = report.get("original_id", report.get("id", "unknown"))
        source = report.get("source", "unknown")
        
        # Common metadata for all chunks
        base_metadata = {
            "vuln_class": report.get("vuln_class", "Other"),
            "severity": report.get("severity", "medium"),
            "cwe": report.get("cwe"),
            "keywords": report.get("keywords", []),
            "title": report.get("title", ""),
            "original_url": report.get("original_url"),
        }
        
        # Generate each chunk type
        chunk_types_to_create = ["attack_pattern", "test_hints", "remediation"]
        if include_full:
            chunk_types_to_create.append("full_context")
        
        for chunk_type in chunk_types_to_create:
            config = self.CHUNK_TYPES[chunk_type]
            
            # Check if we have required fields
            has_content = any(
                report.get(field) for field in config["fields"]
            )
            
            if not has_content:
                continue
            
            # Build content from template
            template_vars = {}
            for field in config["fields"]:
                value = report.get(field, "")
                if isinstance(value, list):
                    value = "\n- " + "\n- ".join(value) if value else ""
                template_vars[field] = value
            
            # Special handling for test_hints list
            if "test_hints" in template_vars:
                hints = report.get("test_hints", [])
                template_vars["test_hints_str"] = "\n- " + "\n- ".join(hints) if hints else ""
            
            try:
                content = config["template"].format(**template_vars)
            except KeyError:
                content = str(template_vars)
            
            # Skip empty or very short chunks
            if len(content.strip()) < 50:
                continue
            
            chunk = ReportChunk(
                id=self._generate_chunk_id(report_id, chunk_type),
                report_id=report_id,
                source=source,
                chunk_type=chunk_type,
                content=content,
                metadata={**base_metadata, "chunk_description": config["description"]},
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def chunk_all_reports(self) -> list[ReportChunk]:
        """
        Chunk all processed reports.
        
        Returns:
            List of all chunks from all reports
        """
        all_chunks = []
        processed_files = list(self.processed_dir.glob("*.json"))
        
        console.print(f"[cyan]Chunking {len(processed_files)} processed reports...[/cyan]")
        
        for filepath in processed_files:
            report = self._load_processed_report(filepath)
            if not report:
                continue
            
            chunks = self.chunk_report(report)
            all_chunks.extend(chunks)
        
        console.print(f"[green]Created {len(all_chunks)} chunks from {len(processed_files)} reports[/green]")
        
        # Stats by chunk type
        type_counts = {}
        for chunk in all_chunks:
            type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
        
        for ctype, count in sorted(type_counts.items()):
            console.print(f"  [dim]- {ctype}: {count}[/dim]")
        
        return all_chunks
    
    def get_chunks_by_vuln_class(self, chunks: list[ReportChunk], vuln_class: str) -> list[ReportChunk]:
        """Filter chunks by vulnerability class."""
        return [
            c for c in chunks 
            if c.metadata.get("vuln_class", "").lower() == vuln_class.lower()
        ]
    
    def get_chunks_by_type(self, chunks: list[ReportChunk], chunk_type: str) -> list[ReportChunk]:
        """Filter chunks by chunk type."""
        return [c for c in chunks if c.chunk_type == chunk_type]
    
    def export_for_embedding(self, chunks: list[ReportChunk]) -> list[dict]:
        """
        Export chunks in format suitable for embedding/vectorization.
        
        Returns:
            List of dicts with 'id', 'text', and 'metadata' keys
        """
        return [
            {
                "id": chunk.id,
                "text": chunk.content,
                "metadata": {
                    **chunk.metadata,
                    "report_id": chunk.report_id,
                    "source": chunk.source,
                    "chunk_type": chunk.chunk_type,
                }
            }
            for chunk in chunks
        ]


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    chunker = ReportChunker(data_dir)
    
    chunks = chunker.chunk_all_reports()
    print(f"\nTotal chunks: {len(chunks)}")
    
    if chunks:
        print("\nSample chunk:")
        print(f"  Type: {chunks[0].chunk_type}")
        print(f"  Content preview: {chunks[0].content[:200]}...")
