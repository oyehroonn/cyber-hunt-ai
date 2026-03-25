"""
ChromaDB Vector Store

Manages persistent vector storage for security vulnerability report chunks.
"""

import json
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class SearchResult:
    """A single search result from the vector store."""
    id: str
    content: str
    metadata: dict
    distance: float
    
    @property
    def similarity(self) -> float:
        """Convert distance to similarity score."""
        return 1.0 - self.distance


class ChromaStore:
    """ChromaDB-based vector store for security reports."""
    
    COLLECTION_NAMES = {
        "vuln_reports": "Main collection of all vulnerability report chunks",
        "test_hints": "Extracted test hints per vulnerability class",
        "remediation": "Remediation patterns per vulnerability class",
    }
    
    def __init__(self, data_dir: Path, embedding_model: str = "all-MiniLM-L6-v2"):
        self.data_dir = Path(data_dir)
        self.chroma_dir = self.data_dir / "chroma_db"
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model = embedding_model
        
        self._client = None
        self._embedding_fn = None
        self._collections = {}
    
    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                self._client = chromadb.PersistentClient(
                    path=str(self.chroma_dir),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    )
                )
            except ImportError:
                console.print("[red]chromadb not installed. Install with: pip install chromadb[/red]")
                raise
        return self._client
    
    def _get_embedding_function(self):
        """Get or create embedding function.

        Tries SentenceTransformer first (best quality), falls back to
        ChromaDB's built-in ONNX-based DefaultEmbeddingFunction which
        avoids PyTorch/NumPy version incompatibilities.
        """
        if self._embedding_fn is None:
            # Try SentenceTransformer (PyTorch-based, best results)
            try:
                from chromadb.utils import embedding_functions
                fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model
                )
                # Probe it with a dummy call to catch NumPy/torch issues early
                fn(["probe"])
                self._embedding_fn = fn
            except Exception:
                pass

            # Fall back to ChromaDB's built-in ONNX embedding (no torch required)
            if self._embedding_fn is None:
                try:
                    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                    self._embedding_fn = DefaultEmbeddingFunction()
                except Exception:
                    pass

            if self._embedding_fn is None:
                raise RuntimeError(
                    "No embedding function available. "
                    "Install chromadb[default] or sentence-transformers."
                )
        return self._embedding_fn
    
    def _get_collection(self, name: str):
        """Get or create a collection."""
        if name not in self._collections:
            client = self._get_client()
            embedding_fn = self._get_embedding_function()
            
            self._collections[name] = client.get_or_create_collection(
                name=name,
                embedding_function=embedding_fn,
                metadata={"description": self.COLLECTION_NAMES.get(name, "")},
            )
        return self._collections[name]
    
    def embed_and_store(self, chunks: list[dict], collection_name: str = "vuln_reports",
                        batch_size: int = 100) -> int:
        """
        Batch embed and insert chunks into vector store.
        
        Args:
            chunks: List of chunk dicts with 'id', 'text'/'content', and 'metadata' keys
            collection_name: Target collection name
            batch_size: Number of chunks to process at once
            
        Returns:
            Number of chunks inserted
        """
        if not chunks:
            return 0
        
        collection = self._get_collection(collection_name)
        
        console.print(f"[cyan]Embedding and storing {len(chunks)} chunks to '{collection_name}'...[/cyan]")
        
        # Get existing IDs to avoid duplicates
        existing_ids = set()
        try:
            result = collection.get()
            existing_ids = set(result.get("ids", []))
        except Exception:
            pass
        
        # Filter out existing chunks
        new_chunks = [c for c in chunks if c.get("id") not in existing_ids]
        
        if not new_chunks:
            console.print("[dim]All chunks already exist in collection[/dim]")
            return 0
        
        console.print(f"[dim]Inserting {len(new_chunks)} new chunks (skipping {len(chunks) - len(new_chunks)} existing)[/dim]")
        
        # Process in batches
        inserted = 0
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]
            
            ids = [c["id"] for c in batch]
            documents = [c.get("text", c.get("content", "")) for c in batch]
            metadatas = [self._sanitize_metadata(c.get("metadata", {})) for c in batch]
            
            try:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )
                inserted += len(batch)
            except Exception as e:
                console.print(f"[red]Error inserting batch: {e}[/red]")
        
        console.print(f"[green]Inserted {inserted} chunks[/green]")
        return inserted
    
    def _sanitize_metadata(self, metadata: dict) -> dict:
        """Sanitize metadata for ChromaDB (must be str, int, float, or bool)."""
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # Convert list to comma-separated string
                sanitized[key] = ", ".join(str(v) for v in value)
            else:
                # Convert other types to string
                sanitized[key] = str(value)
        return sanitized
    
    def similarity_search(self, query: str, n_results: int = 5,
                          collection_name: str = "vuln_reports",
                          filter_metadata: Optional[dict] = None) -> list[SearchResult]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            collection_name: Collection to search
            filter_metadata: Optional metadata filters (e.g., {"vuln_class": "IDOR"})
            
        Returns:
            List of SearchResult objects
        """
        collection = self._get_collection(collection_name)
        
        where_filter = None
        if filter_metadata:
            where_filter = {
                "$and": [
                    {key: {"$eq": value}}
                    for key, value in filter_metadata.items()
                ]
            }
            if len(filter_metadata) == 1:
                key, value = list(filter_metadata.items())[0]
                where_filter = {key: {"$eq": value}}
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            search_results = []
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc_id in enumerate(ids):
                search_results.append(SearchResult(
                    id=doc_id,
                    content=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    distance=distances[i] if i < len(distances) else 1.0,
                ))

            return search_results

        except Exception:
            # Embedding computation failed (e.g. NumPy/torch version mismatch).
            # Fall back to keyword-based retrieval using collection.get().
            return self._keyword_search(
                collection, query, n_results, where_filter
            )

    def _keyword_search(
        self,
        collection,
        query: str,
        n_results: int,
        where_filter=None,
    ) -> list["SearchResult"]:
        """
        Keyword-based fallback when embedding similarity search is unavailable.
        Scores documents by term overlap with the query (simple TF-IDF proxy).
        """
        try:
            kwargs: dict = {"include": ["documents", "metadatas"]}
            if where_filter:
                kwargs["where"] = where_filter

            # Fetch up to 500 docs; increase limit for very large collections
            result = collection.get(limit=500, **kwargs)
            ids = result.get("ids", [])
            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])

            if not ids:
                return []

            # Simple BM25-style keyword score
            query_terms = set(query.lower().split())
            scores: list[tuple[float, int]] = []
            for i, doc in enumerate(documents):
                if not doc:
                    continue
                doc_terms = doc.lower().split()
                doc_term_set = set(doc_terms)
                overlap = len(query_terms & doc_term_set)
                # Bonus for exact phrase match
                phrase_bonus = 2.0 if query.lower() in doc.lower() else 0.0
                score = overlap + phrase_bonus
                scores.append((score, i))

            scores.sort(key=lambda x: x[0], reverse=True)
            top = scores[:n_results]

            search_results = []
            for score, i in top:
                if score == 0:
                    continue
                # Convert keyword score to pseudo-distance (lower = better)
                max_score = scores[0][0] if scores else 1
                distance = 1.0 - (score / max(max_score, 1))
                search_results.append(SearchResult(
                    id=ids[i] if i < len(ids) else f"kw_{i}",
                    content=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    distance=distance,
                ))

            return search_results

        except Exception:
            return []
    
    def get_by_vuln_class(self, vuln_class: str, n_results: int = 10,
                          collection_name: str = "vuln_reports") -> list[SearchResult]:
        """
        Get chunks filtered by vulnerability class.
        
        Args:
            vuln_class: Vulnerability class to filter by
            n_results: Maximum number of results
            collection_name: Collection to search
            
        Returns:
            List of SearchResult objects
        """
        collection = self._get_collection(collection_name)
        
        try:
            results = collection.get(
                where={"vuln_class": {"$eq": vuln_class}},
                limit=n_results,
                include=["documents", "metadatas"],
            )
            
            search_results = []
            ids = results.get("ids", [])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            for i, doc_id in enumerate(ids):
                search_results.append(SearchResult(
                    id=doc_id,
                    content=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    distance=0.0,  # No distance for direct retrieval
                ))
            
            return search_results
            
        except Exception as e:
            console.print(f"[red]Get by class error: {e}[/red]")
            return []
    
    def get_collection_stats(self, collection_name: str = "vuln_reports") -> dict:
        """Get statistics about a collection."""
        collection = self._get_collection(collection_name)
        
        try:
            count = collection.count()
            
            # Get sample to analyze metadata
            sample = collection.get(limit=100, include=["metadatas"])
            
            vuln_classes = {}
            severities = {}
            sources = {}
            
            for meta in sample.get("metadatas", []):
                vc = meta.get("vuln_class", "Unknown")
                vuln_classes[vc] = vuln_classes.get(vc, 0) + 1
                
                sev = meta.get("severity", "Unknown")
                severities[sev] = severities.get(sev, 0) + 1
                
                src = meta.get("source", "Unknown")
                sources[src] = sources.get(src, 0) + 1
            
            return {
                "total_chunks": count,
                "vuln_classes": vuln_classes,
                "severities": severities,
                "sources": sources,
            }
            
        except Exception as e:
            console.print(f"[dim]Stats error: {e}[/dim]")
            return {"total_chunks": 0}
    
    def print_stats(self):
        """Print statistics for all collections."""
        console.print("\n[bold]Vector Store Statistics[/bold]\n")
        
        for collection_name in self.COLLECTION_NAMES:
            stats = self.get_collection_stats(collection_name)
            
            table = Table(title=f"Collection: {collection_name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total chunks", str(stats.get("total_chunks", 0)))
            
            # Vuln class breakdown
            vuln_classes = stats.get("vuln_classes", {})
            if vuln_classes:
                top_classes = sorted(vuln_classes.items(), key=lambda x: x[1], reverse=True)[:5]
                for vc, count in top_classes:
                    table.add_row(f"  {vc}", str(count))
            
            console.print(table)
            console.print()
    
    def delete_collection(self, collection_name: str):
        """Delete a collection."""
        client = self._get_client()
        try:
            client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
            console.print(f"[green]Deleted collection: {collection_name}[/green]")
        except Exception as e:
            console.print(f"[red]Error deleting collection: {e}[/red]")
    
    def reset(self):
        """Reset all collections (delete all data)."""
        client = self._get_client()
        try:
            client.reset()
            self._collections = {}
            console.print("[yellow]Reset all collections[/yellow]")
        except Exception as e:
            console.print(f"[red]Error resetting: {e}[/red]")
    
    def get_total_chunks(self) -> int:
        """Get total number of chunks across all collections."""
        total = 0
        for collection_name in self.COLLECTION_NAMES:
            stats = self.get_collection_stats(collection_name)
            total += stats.get("total_chunks", 0)
        return total


def create_store(data_dir: Path) -> ChromaStore:
    """Factory function to create a ChromaStore instance."""
    return ChromaStore(data_dir)


if __name__ == "__main__":
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / "data"
    store = ChromaStore(data_dir)
    
    # Test with sample data
    sample_chunks = [
        {
            "id": "test_1",
            "text": "SQL injection vulnerability in the search parameter allows attackers to execute arbitrary queries.",
            "metadata": {"vuln_class": "SQL Injection", "severity": "high", "source": "test"},
        },
        {
            "id": "test_2",
            "text": "IDOR vulnerability allows users to access other users' data by modifying the user_id parameter.",
            "metadata": {"vuln_class": "IDOR", "severity": "medium", "source": "test"},
        },
    ]
    
    # Store chunks
    store.embed_and_store(sample_chunks)
    
    # Search
    results = store.similarity_search("How to find SQL injection?", n_results=3)
    print("\nSearch results:")
    for r in results:
        print(f"  [{r.similarity:.2f}] {r.content[:80]}...")
    
    # Print stats
    store.print_stats()
