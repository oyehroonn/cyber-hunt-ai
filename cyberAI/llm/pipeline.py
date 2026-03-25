#!/usr/bin/env python3
"""
RAG Pipeline Runner

End-to-end pipeline for scraping, processing, embedding, and testing
the security vulnerability knowledge base.

Usage (from repository root):
    python3 cyberAI/llm/pipeline.py scrape       # Run all scrapers
    python3 cyberAI/llm/pipeline.py process      # Summarize raw reports
    python3 cyberAI/llm/pipeline.py embed        # Chunk, deduplicate, embed
    python3 cyberAI/llm/pipeline.py test         # Run test queries
    python3 cyberAI/llm/pipeline.py full         # Run full pipeline
    python3 cyberAI/llm/pipeline.py status       # Print system status
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from repository root (parent of cyberAI/) — same as cyberAI.main / llm_client
try:
    from llm.project_env import get_openai_compatible_llm_config, load_project_dotenv

    load_project_dotenv()
except ImportError:
    get_openai_compatible_llm_config = None  # type: ignore[misc, assignment]

console = Console()


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent / "data"


def cmd_scrape(max_per_source: int = 60, sources: Optional[list[str]] = None):
    """Run all scrapers to collect raw reports."""
    from llm.scraper.hackerone_scraper import HackerOneScraper
    from llm.scraper.bugcrowd_scraper import BugcrowdScraper
    from llm.scraper.portswigger_scraper import PortSwiggerScraper
    from llm.scraper.github_scraper import GitHubAdvisoryScraper
    from llm.scraper.cve_scraper import CVEScraper
    from llm.scraper.cwe_scraper import CWEScraper
    from llm.scraper.exploitdb_scraper import ExploitDBScraper
    from llm.scraper.payloads_scraper import PayloadsScraper
    from llm.scraper.general_scraper import GeneralScraper
    
    data_dir = get_data_dir()
    
    # Scrapers ordered by reliability (most reliable first)
    all_scrapers = {
        "cve": (CVEScraper, 80),           # NVD API - very reliable
        "cwe": (CWEScraper, 50),            # MITRE CWE - very reliable
        "portswigger": (PortSwiggerScraper, 50),  # Static pages - reliable
        "general": (GeneralScraper, 60),   # OWASP cheat sheets - reliable
        "payloads": (PayloadsScraper, 30), # PayloadsAllTheThings - reliable
        "exploitdb": (ExploitDBScraper, 40),  # Exploit-DB - mostly reliable
        "github": (GitHubAdvisoryScraper, 30),  # GitHub API - may have rate limits
        "hackerone": (HackerOneScraper, 20),   # Needs JS - limited
        "bugcrowd": (BugcrowdScraper, 10),     # Needs auth - limited
    }
    
    # Filter to requested sources
    if sources:
        scrapers = {k: v for k, v in all_scrapers.items() if k in sources}
    else:
        scrapers = all_scrapers
    
    total_scraped = 0
    
    console.print(Panel.fit(
        "[bold cyan]Security Report Scraper[/bold cyan]\n"
        f"Sources: {', '.join(scrapers.keys())}\n"
        f"Target: {sum(v[1] for v in scrapers.values())}+ reports",
        title="RAG Pipeline - Scrape"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        for source_name, (scraper_class, default_max) in scrapers.items():
            max_reports = min(max_per_source, default_max) if max_per_source else default_max
            
            task = progress.add_task(
                f"[cyan]{source_name}[/cyan]",
                total=max_reports
            )
            
            try:
                with scraper_class(data_dir) as scraper:
                    # Check existing
                    existing = scraper.get_existing_count()
                    if existing >= max_reports:
                        console.print(f"[dim]Skipping {source_name}: {existing} reports already exist[/dim]")
                        progress.update(task, completed=max_reports)
                        continue
                    
                    reports = scraper.scrape(
                        max_reports=max_reports - existing,
                        progress=progress,
                        task=task
                    )
                    total_scraped += len(reports)
                    
            except Exception as e:
                console.print(f"[red]Error scraping {source_name}: {e}[/red]")
                progress.update(task, completed=max_reports)
    
    # Print summary
    raw_dir = data_dir / "raw"
    total_files = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
    
    console.print(f"\n[green]Scraping complete![/green]")
    console.print(f"New reports scraped: {total_scraped}")
    console.print(f"Total raw reports: {total_files}")


def cmd_process(use_llm: bool = False):
    """Process raw reports into structured format."""
    from llm.processor.summarizer import ReportSummarizer
    from llm.rag_engine import RAGEngine
    
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    
    if not raw_dir.exists() or not list(raw_dir.glob("*.json")):
        console.print("[yellow]No raw reports found. Run 'scrape' first.[/yellow]")
        return
    
    raw_count = len(list(raw_dir.glob("*.json")))
    
    console.print(Panel.fit(
        f"[bold cyan]Report Processor[/bold cyan]\n"
        f"Raw reports: {raw_count}\n"
        f"LLM summarization: {'Enabled' if use_llm else 'Disabled (fallback mode)'}",
        title="RAG Pipeline - Process"
    ))
    
    # Initialize summarizer
    llm_client = None
    if use_llm:
        try:
            engine = RAGEngine(data_dir)
            if engine.model_name:
                llm_client = engine
                console.print(f"[green]Using LLM: {engine.model_name}[/green]")
            else:
                console.print("[yellow]No LLM available, using fallback summarization[/yellow]")
        except Exception as e:
            console.print(f"[yellow]LLM unavailable ({e}), using fallback[/yellow]")
    
    summarizer = ReportSummarizer(data_dir, llm_client=llm_client)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing reports[/cyan]", total=raw_count)
        processed = summarizer.process_all(use_llm=use_llm, progress=progress, task=task)
    
    console.print(f"\n[green]Processing complete![/green]")
    console.print(f"New reports processed: {len(processed)}")
    console.print(f"Total processed reports: {summarizer.get_processed_count()}")


def cmd_embed():
    """Chunk, deduplicate, and embed processed reports."""
    from llm.processor.chunker import ReportChunker
    from llm.processor.deduplicator import ReportDeduplicator
    from llm.vector_store.chroma_store import ChromaStore
    
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    
    if not processed_dir.exists() or not list(processed_dir.glob("*.json")):
        console.print("[yellow]No processed reports found. Run 'process' first.[/yellow]")
        return
    
    processed_count = len(list(processed_dir.glob("*.json")))
    
    console.print(Panel.fit(
        f"[bold cyan]Embedding Pipeline[/bold cyan]\n"
        f"Processed reports: {processed_count}",
        title="RAG Pipeline - Embed"
    ))
    
    # Step 1: Chunk reports
    console.print("\n[cyan]Step 1: Chunking reports...[/cyan]")
    chunker = ReportChunker(data_dir)
    chunks = chunker.chunk_all_reports()
    
    if not chunks:
        console.print("[yellow]No chunks generated[/yellow]")
        return
    
    # Step 2: Deduplicate
    console.print("\n[cyan]Step 2: Deduplicating chunks...[/cyan]")
    try:
        deduplicator = ReportDeduplicator(similarity_threshold=0.92)
        chunk_dicts = [c.to_dict() for c in chunks]
        
        # Add text field for deduplicator
        for cd in chunk_dicts:
            cd["text"] = cd["content"]
        
        deduplicated, result = deduplicator.deduplicate(chunk_dicts)
    except ImportError:
        console.print("[yellow]sentence-transformers not installed, skipping deduplication[/yellow]")
        deduplicated = [c.to_dict() for c in chunks]
        for cd in deduplicated:
            cd["text"] = cd["content"]
    
    # Step 3: Embed and store
    console.print("\n[cyan]Step 3: Embedding and storing...[/cyan]")
    store = ChromaStore(data_dir)
    
    # Format for embedding
    embed_chunks = [
        {
            "id": c["id"],
            "text": c["content"],
            "metadata": c["metadata"],
        }
        for c in deduplicated
    ]
    
    inserted = store.embed_and_store(embed_chunks, collection_name="vuln_reports")
    
    # Also create specialized collections
    console.print("\n[cyan]Creating specialized collections...[/cyan]")
    
    # Test hints collection
    test_hint_chunks = [c for c in embed_chunks if "test_hints" in c.get("metadata", {}).get("chunk_type", "")]
    if test_hint_chunks:
        store.embed_and_store(test_hint_chunks, collection_name="test_hints")
    
    # Remediation collection
    remediation_chunks = [c for c in embed_chunks if "remediation" in c.get("metadata", {}).get("chunk_type", "")]
    if remediation_chunks:
        store.embed_and_store(remediation_chunks, collection_name="remediation")
    
    console.print(f"\n[green]Embedding complete![/green]")
    store.print_stats()


def cmd_test():
    """Run test queries against the knowledge base."""
    from llm.vector_store.chroma_store import ChromaStore
    from llm.rag_engine import RAGEngine
    
    data_dir = get_data_dir()
    store = ChromaStore(data_dir)
    
    if store.get_total_chunks() == 0:
        console.print("[yellow]No chunks in vector store. Run 'embed' first.[/yellow]")
        return
    
    console.print(Panel.fit(
        "[bold cyan]RAG Test Queries[/bold cyan]",
        title="RAG Pipeline - Test"
    ))
    
    # Test queries by vulnerability class
    test_queries = [
        ("IDOR vulnerability patterns", "IDOR"),
        ("SQL injection attack techniques", "SQL Injection"),
        ("Authentication bypass methods", "Authentication Bypass"),
        ("Business logic vulnerability testing", "Business Logic"),
        ("SSRF server-side request forgery", "SSRF"),
        ("Race condition exploitation", "Race Condition"),
    ]
    
    for query, vuln_class in test_queries:
        console.print(f"\n[cyan]Query: {query}[/cyan]")
        
        results = store.similarity_search(query, n_results=3)
        
        if results:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Similarity", style="green", width=10)
            table.add_column("Type", style="cyan", width=20)
            table.add_column("Content Preview", width=60)
            
            for r in results:
                table.add_row(
                    f"{r.similarity:.3f}",
                    r.metadata.get("vuln_class", "Unknown"),
                    r.content[:80] + "..." if len(r.content) > 80 else r.content
                )
            
            console.print(table)
        else:
            console.print("[dim]No results found[/dim]")
    
    # Test LLM if available
    console.print("\n[cyan]Testing LLM generation...[/cyan]")
    try:
        engine = RAGEngine(data_dir)
        if engine.model_name:
            client = engine._get_llm_client()
            if client.is_available():
                console.print(f"[green]LLM available: {engine.model_name}[/green]")
                
                # Quick test
                response = engine.generate(
                    "List 3 common {vuln_type} attack patterns.",
                    {"vuln_type": "IDOR"},
                    n_context=2
                )
                console.print(f"\n[dim]Sample response:\n{response[:500]}...[/dim]")
            else:
                console.print("[yellow]LLM model not loaded. Pull with: ollama pull {engine.model_name}[/yellow]")
        else:
            console.print("[yellow]No LLM model selected[/yellow]")
    except Exception as e:
        console.print(f"[yellow]LLM test skipped: {e}[/yellow]")


def cmd_status():
    """Print comprehensive system status."""
    from llm.model_selector import ModelSelector
    from llm.vector_store.chroma_store import ChromaStore
    
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    console.print(Panel.fit(
        "[bold cyan]RAG Pipeline Status[/bold cyan]",
        title="System Status"
    ))
    
    # Data statistics
    raw_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
    processed_count = len(list(processed_dir.glob("*.json"))) if processed_dir.exists() else 0
    
    # Count by source
    source_counts = {}
    if raw_dir.exists():
        for f in raw_dir.glob("*.json"):
            source = f.stem.split("_")[0]
            source_counts[source] = source_counts.get(source, 0) + 1
    
    data_table = Table(title="Data Statistics")
    data_table.add_column("Metric", style="cyan")
    data_table.add_column("Value", style="green")
    
    data_table.add_row("Raw reports", str(raw_count))
    data_table.add_row("Processed reports", str(processed_count))
    
    for source, count in sorted(source_counts.items()):
        data_table.add_row(f"  └─ {source}", str(count))
    
    console.print(data_table)
    
    # Vector store statistics
    try:
        store = ChromaStore(data_dir)
        store.print_stats()
    except Exception as e:
        console.print(f"[dim]Vector store not initialized: {e}[/dim]")
    
    # Model status
    console.print()
    cfg = (
        get_openai_compatible_llm_config()
        if get_openai_compatible_llm_config
        else None
    )
    if cfg and cfg.api_key:
        console.print("[green]LLM: API (OpenAI-compatible)[/green]")
        console.print(f"  Base URL: {cfg.base_url}")
        console.print(f"  Model: {cfg.model}")
        if cfg.extra_headers:
            console.print("  [dim]Extra headers: OpenRouter referer/title[/dim]")
        console.print("  [dim]No local Ollama needed.[/dim]")
    else:
        selector = ModelSelector()
        model = selector.initialize()
        selector.print_status()
        if not model:
            console.print("\n[yellow]Setup required:[/yellow]")
            selector.print_setup_guide()


def cmd_full(max_per_source: int = 60, use_llm: bool = False):
    """Run full pipeline: scrape → process → embed → test."""
    console.print(Panel.fit(
        "[bold cyan]Full RAG Pipeline[/bold cyan]\n"
        "scrape → process → embed → test",
        title="RAG Pipeline - Full"
    ))
    
    console.print("\n[bold]Step 1/4: Scraping reports...[/bold]")
    cmd_scrape(max_per_source=max_per_source)
    
    console.print("\n[bold]Step 2/4: Processing reports...[/bold]")
    cmd_process(use_llm=use_llm)
    
    console.print("\n[bold]Step 3/4: Embedding reports...[/bold]")
    cmd_embed()
    
    console.print("\n[bold]Step 4/4: Testing queries...[/bold]")
    cmd_test()
    
    console.print("\n" + "=" * 60)
    console.print("[bold green]Full pipeline complete![/bold green]")
    cmd_status()


def main():
    parser = argparse.ArgumentParser(
        description="RAG Pipeline for Security Vulnerability Knowledge Base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  scrape     Scrape vulnerability reports from multiple sources
  process    Summarize and structure raw reports
  embed      Chunk, deduplicate, and embed into vector store
  test       Run test queries against the knowledge base
  full       Run the full pipeline (scrape → process → embed → test)
  status     Print system status and statistics

Examples:
  python3 cyberAI/llm/pipeline.py status
  python3 cyberAI/llm/pipeline.py scrape --max-per-source 20
  python3 cyberAI/llm/pipeline.py process --use-llm
  python3 cyberAI/llm/pipeline.py full
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Pipeline command")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape vulnerability reports")
    scrape_parser.add_argument(
        "--max-per-source", "-m", type=int, default=60,
        help="Maximum reports to scrape per source (default: 60)"
    )
    scrape_parser.add_argument(
        "--sources", "-s", nargs="+",
        choices=["hackerone", "bugcrowd", "portswigger", "github", "cve", "general"],
        help="Specific sources to scrape (default: all)"
    )
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process raw reports")
    process_parser.add_argument(
        "--use-llm", "-l", action="store_true",
        help="Use LLM for summarization (requires Ollama)"
    )
    
    # Embed command
    subparsers.add_parser("embed", help="Embed processed reports into vector store")
    
    # Test command
    subparsers.add_parser("test", help="Run test queries")
    
    # Status command
    subparsers.add_parser("status", help="Print system status")
    
    # Full command
    full_parser = subparsers.add_parser("full", help="Run full pipeline")
    full_parser.add_argument(
        "--max-per-source", "-m", type=int, default=60,
        help="Maximum reports to scrape per source"
    )
    full_parser.add_argument(
        "--use-llm", "-l", action="store_true",
        help="Use LLM for processing"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        if args.command == "scrape":
            cmd_scrape(max_per_source=args.max_per_source, sources=args.sources)
        elif args.command == "process":
            cmd_process(use_llm=args.use_llm)
        elif args.command == "embed":
            cmd_embed()
        elif args.command == "test":
            cmd_test()
        elif args.command == "status":
            cmd_status()
        elif args.command == "full":
            cmd_full(max_per_source=args.max_per_source, use_llm=args.use_llm)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
