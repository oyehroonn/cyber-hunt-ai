"""
Report Deduplicator

Detects and removes near-duplicate reports using embedding similarity.
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class DuplicationResult:
    """Result of deduplication analysis."""
    original_count: int
    unique_count: int
    duplicates_removed: int
    duplicate_pairs: list[tuple[str, str, float]]


class ReportDeduplicator:
    """Removes near-duplicate reports using embedding similarity."""
    
    DEFAULT_THRESHOLD = 0.92  # Cosine similarity threshold for considering duplicates
    
    def __init__(self, similarity_threshold: float = DEFAULT_THRESHOLD):
        self.threshold = similarity_threshold
        self._embedder = None
    
    def _get_embedder(self):
        """Lazy load sentence transformer embedder."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                console.print("[red]sentence-transformers not installed. Install with: pip install sentence-transformers[/red]")
                raise
        return self._embedder
    
    def _compute_embeddings(self, texts: list[str]) -> np.ndarray:
        """Compute embeddings for a list of texts."""
        embedder = self._get_embedder()
        return embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def _compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity matrix."""
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms
        # Compute similarity matrix
        return np.dot(normalized, normalized.T)
    
    def find_duplicates(self, chunks: list[dict]) -> list[tuple[int, int, float]]:
        """
        Find duplicate pairs among chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'id' and 'text' keys
            
        Returns:
            List of (index_a, index_b, similarity) tuples for duplicates
        """
        if len(chunks) < 2:
            return []
        
        console.print(f"[cyan]Computing embeddings for {len(chunks)} chunks...[/cyan]")
        
        # Extract texts
        texts = [c.get("text", c.get("content", "")) for c in chunks]
        
        # Compute embeddings
        embeddings = self._compute_embeddings(texts)
        
        # Compute similarity matrix
        console.print("[cyan]Computing similarity matrix...[/cyan]")
        sim_matrix = self._compute_similarity_matrix(embeddings)
        
        # Find pairs above threshold
        duplicates = []
        n = len(chunks)
        
        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i, j] >= self.threshold:
                    duplicates.append((i, j, float(sim_matrix[i, j])))
        
        console.print(f"[dim]Found {len(duplicates)} duplicate pairs[/dim]")
        return duplicates
    
    def deduplicate(self, chunks: list[dict], keep_longer: bool = True) -> tuple[list[dict], DuplicationResult]:
        """
        Remove duplicate chunks, keeping the more detailed version.
        
        Args:
            chunks: List of chunk dictionaries
            keep_longer: If True, keep the longer chunk; if False, keep the first one
            
        Returns:
            Tuple of (deduplicated chunks, deduplication stats)
        """
        if len(chunks) < 2:
            return chunks, DuplicationResult(
                original_count=len(chunks),
                unique_count=len(chunks),
                duplicates_removed=0,
                duplicate_pairs=[],
            )
        
        # Find duplicates
        duplicate_pairs = self.find_duplicates(chunks)
        
        if not duplicate_pairs:
            return chunks, DuplicationResult(
                original_count=len(chunks),
                unique_count=len(chunks),
                duplicates_removed=0,
                duplicate_pairs=[],
            )
        
        # Determine which indices to remove
        indices_to_remove = set()
        pair_details = []
        
        for i, j, similarity in duplicate_pairs:
            if i in indices_to_remove or j in indices_to_remove:
                continue  # Skip if one is already marked for removal
            
            chunk_i = chunks[i]
            chunk_j = chunks[j]
            
            text_i = chunk_i.get("text", chunk_i.get("content", ""))
            text_j = chunk_j.get("text", chunk_j.get("content", ""))
            
            id_i = chunk_i.get("id", str(i))
            id_j = chunk_j.get("id", str(j))
            
            # Decide which to keep
            if keep_longer:
                if len(text_j) > len(text_i):
                    indices_to_remove.add(i)
                    pair_details.append((id_i, id_j, similarity))
                else:
                    indices_to_remove.add(j)
                    pair_details.append((id_j, id_i, similarity))
            else:
                indices_to_remove.add(j)
                pair_details.append((id_j, id_i, similarity))
        
        # Filter out removed indices
        deduplicated = [
            chunk for idx, chunk in enumerate(chunks)
            if idx not in indices_to_remove
        ]
        
        result = DuplicationResult(
            original_count=len(chunks),
            unique_count=len(deduplicated),
            duplicates_removed=len(indices_to_remove),
            duplicate_pairs=pair_details,
        )
        
        self._log_deduplication(result)
        
        return deduplicated, result
    
    def _log_deduplication(self, result: DuplicationResult):
        """Log deduplication statistics."""
        table = Table(title="Deduplication Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Original chunks", str(result.original_count))
        table.add_row("Unique chunks", str(result.unique_count))
        table.add_row("Duplicates removed", str(result.duplicates_removed))
        table.add_row("Reduction", f"{(result.duplicates_removed / result.original_count * 100):.1f}%" if result.original_count > 0 else "0%")
        
        console.print(table)
        
        if result.duplicate_pairs and len(result.duplicate_pairs) <= 10:
            console.print("\n[dim]Sample duplicate pairs:[/dim]")
            for removed, kept, sim in result.duplicate_pairs[:5]:
                console.print(f"  [dim]Removed {removed[:12]}... (kept {kept[:12]}..., similarity: {sim:.3f})[/dim]")
    
    def deduplicate_by_vuln_class(self, chunks: list[dict]) -> tuple[list[dict], dict[str, DuplicationResult]]:
        """
        Deduplicate chunks within each vulnerability class separately.
        
        This is more conservative - only removes duplicates within the same vuln class.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Tuple of (deduplicated chunks, per-class results)
        """
        # Group by vuln_class
        by_class = {}
        for chunk in chunks:
            vuln_class = chunk.get("metadata", {}).get("vuln_class", "Other")
            if vuln_class not in by_class:
                by_class[vuln_class] = []
            by_class[vuln_class].append(chunk)
        
        # Deduplicate each class
        deduplicated = []
        class_results = {}
        
        for vuln_class, class_chunks in by_class.items():
            console.print(f"\n[cyan]Deduplicating {vuln_class} ({len(class_chunks)} chunks)...[/cyan]")
            
            deduped, result = self.deduplicate(class_chunks)
            deduplicated.extend(deduped)
            class_results[vuln_class] = result
        
        return deduplicated, class_results


def deduplicate_chunks(chunks: list[dict], threshold: float = 0.92) -> list[dict]:
    """
    Convenience function to deduplicate a list of chunks.
    
    Args:
        chunks: List of chunk dictionaries with 'text' and optional 'id' keys
        threshold: Cosine similarity threshold (default 0.92)
        
    Returns:
        Deduplicated list of chunks
    """
    deduplicator = ReportDeduplicator(similarity_threshold=threshold)
    deduplicated, _ = deduplicator.deduplicate(chunks)
    return deduplicated


if __name__ == "__main__":
    # Test with sample data
    sample_chunks = [
        {"id": "1", "text": "SQL injection vulnerability allows attackers to execute arbitrary SQL queries through unsanitized user input in the search parameter."},
        {"id": "2", "text": "SQL injection flaw enables attackers to run arbitrary SQL queries via unsanitized user input in the search field."},  # Near duplicate
        {"id": "3", "text": "Cross-site scripting (XSS) vulnerability allows injection of malicious JavaScript in the comments section."},
        {"id": "4", "text": "IDOR vulnerability allows users to access other users' private data by modifying the user_id parameter."},
    ]
    
    deduplicator = ReportDeduplicator(similarity_threshold=0.85)
    deduplicated, result = deduplicator.deduplicate(sample_chunks)
    
    print(f"\nKept {len(deduplicated)} unique chunks")
    for chunk in deduplicated:
        print(f"  - {chunk['id']}: {chunk['text'][:50]}...")
