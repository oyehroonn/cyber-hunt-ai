#!/usr/bin/env python3
"""
CyberAI - Enterprise-Grade AI-Powered Cybersecurity Reconnaissance Platform

Master orchestrator for running reconnaissance, planning, testing, verification, and reporting.

Usage:
    python main.py recon --target https://example.com [--role guest,user,admin] [--proxy]
    python main.py plan   [--recon-dir outputs/recon]
    python main.py test   [--plan-dir outputs/planning] [--categories auth,authz,race] [--workers 8]
    python main.py verify [--findings-dir outputs/testing/findings]
    python main.py report [--verified-dir outputs/verification/confirmed]
    python main.py full   --target https://example.com   # runs all phases sequentially
"""

import argparse
import asyncio
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from cyberAI.config import Config, get_config
from cyberAI.utils.helpers import atomic_write_json, generate_run_id
from cyberAI.utils.browser import cleanup_browser_pool
from cyberAI.utils.http_client import cleanup_http_client

console = Console()


def setup_logging(run_id: str, phase: str) -> None:
    """Configure logging for a run."""
    config = get_config()
    log_path = config.get_output_path("logs", f"{phase}_{run_id}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.remove()
    logger.add(sys.stderr, level=config.log_level)
    logger.add(str(log_path), level="DEBUG", rotation="100 MB")
    
    logger.info(f"Starting {phase} phase with run_id: {run_id}")


def write_crash_report(error: Exception, run_id: str) -> None:
    """Write crash report on unhandled exception."""
    config = get_config()
    crash_path = config.get_output_path("logs", f"crash_{run_id}.json")
    
    crash_data = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    
    atomic_write_json(crash_path, crash_data)
    logger.error(f"Crash report written to {crash_path}")


async def run_recon(args) -> dict:
    """Run full reconnaissance phase (all 16 steps)."""
    from pathlib import Path

    from cyberAI.recon import (
        run_account_state_discovery,
        run_async_flow_discovery,
        run_comparison_engine,
        run_core_discovery,
        run_frontend_parser,
        run_input_schema_analysis,
        run_intelligence_aggregation,
        run_object_model_builder,
        run_permission_inference,
        run_role_discovery,
        run_security_controls_analysis,
        run_sensitive_surfaces_discovery,
        run_graphql_discovery,
        run_websocket_discovery,
        run_workflow_mapper,
    )
    from cyberAI.recon.network_intelligence import NetworkIntelligence
    from cyberAI.utils.browser import get_browser_pool

    run_id = args.run_id or generate_run_id()
    setup_logging(run_id, "recon")

    config = get_config()
    config.target_url = args.target or config.target_url or ""

    console.print(Panel(f"[bold cyan]Starting Reconnaissance[/bold cyan]\nTarget: {args.target}", title="CyberAI"))

    results = {"phase": "recon", "run_id": run_id, "target": args.target}

    browser_pool = get_browser_pool()
    await browser_pool.initialize()

    total_steps = 18
    with Progress() as progress:
        task = progress.add_task("[cyan]Running recon phases...", total=total_steps)

        # Step 1: Core discovery with network intel attached to capture requests
        progress.update(task, description="[cyan]Core discovery (crawl + network capture)...")
        context = await browser_pool.get_browser_context(role=None)
        network_intel = NetworkIntelligence(run_id=run_id)
        await network_intel.attach_to_context(context, None)
        routes = await run_core_discovery(
            args.target, role=None, run_id=run_id, context=context, network_intel=network_intel
        )
        await context.close()
        network_intel.save_intelligence()
        results["routes_discovered"] = len(routes)
        progress.advance(task)

        requests = network_intel.get_requests()
        endpoints = network_intel.get_endpoints()

        # Step 2: Network intelligence already captured above; endpoints/requests saved
        progress.update(task, description="[cyan]Network intelligence (saved)...")
        progress.advance(task)

        # Step 3: Frontend parser (HTML from first route DOM if available)
        progress.update(task, description="[cyan]Frontend parser...")
        if routes and routes[0].dom_path and Path(routes[0].dom_path).exists():
            html_content = Path(routes[0].dom_path).read_text()
        else:
            html_content = "<html><head></head><body></body></html>"
        base_url = args.target.rstrip("/") if args.target else ""
        await run_frontend_parser(html_content, base_url, crawled_routes=routes, run_id=run_id)
        progress.advance(task)

        # Step 4: Role discovery (optional; only if role accounts configured)
        role_diffs = []
        if config.role_accounts:
            progress.update(task, description="[cyan]Role discovery...")
            role_discovery = await run_role_discovery(args.target, run_id=run_id)
            role_diffs = role_discovery._role_diffs
            progress.advance(task)
        else:
            progress.update(task, description="[cyan]Role discovery (skipped, no accounts)...")
            progress.advance(task)

        # Step 5: Account state (optional)
        progress.update(task, description="[cyan]Account state discovery...")
        try:
            await run_account_state_discovery(args.target, run_id=run_id)
        except Exception:
            pass
        progress.advance(task)

        # Step 6: Sensitive surfaces
        progress.update(task, description="[cyan]Sensitive surfaces...")
        await run_sensitive_surfaces_discovery(args.target, run_id=run_id)
        progress.advance(task)

        # Step 7: GraphQL discovery
        progress.update(task, description="[cyan]GraphQL discovery...")
        await run_graphql_discovery(args.target, run_id=run_id)
        progress.advance(task)

        # Step 8: WebSocket discovery
        progress.update(task, description="[cyan]WebSocket discovery...")
        await run_websocket_discovery(args.target, run_id=run_id)
        progress.advance(task)

        # Step 9: Async flow discovery
        progress.update(task, description="[cyan]Async flow discovery...")
        await run_async_flow_discovery(requests, run_id=run_id)
        progress.advance(task)

        # Step 10: Object model
        progress.update(task, description="[cyan]Building object models...")
        object_builder = run_object_model_builder(requests, endpoints, run_id=run_id)
        objects = object_builder.get_objects()
        progress.advance(task)

        # Step 11: Permission inference
        progress.update(task, description="[cyan]Inferring permissions...")
        run_permission_inference(role_diffs, endpoints, objects, run_id=run_id)
        progress.advance(task)

        # Step 12: Workflow mapper
        progress.update(task, description="[cyan]Workflow mapper...")
        run_workflow_mapper(routes, requests, run_id=run_id)
        progress.advance(task)

        # Step 13: Input schema analysis
        progress.update(task, description="[cyan]Input schema analysis...")
        run_input_schema_analysis(requests, endpoints, run_id=run_id)
        progress.advance(task)

        # Step 14: Security controls
        progress.update(task, description="[cyan]Analyzing security controls...")
        run_security_controls_analysis(requests, run_id=run_id)
        progress.advance(task)

        # Step 15: Comparison engine (optional; needs roles)
        if config.role_accounts and endpoints:
            progress.update(task, description="[cyan]Comparison engine...")
            roles = [acc.role for acc in config.role_accounts]
            await run_comparison_engine(endpoints, roles, run_id=run_id)
        else:
            progress.update(task, description="[cyan]Comparison engine (skipped)...")
        progress.advance(task)

        # Step 16: Intelligence aggregation
        progress.update(task, description="[cyan]Aggregating intelligence...")
        run_intelligence_aggregation(run_id=run_id)
        progress.advance(task)

        await cleanup_browser_pool()
        progress.advance(task)

    console.print("[green]Reconnaissance complete![/green]")
    return results


async def run_plan(args) -> dict:
    """Run planning phase."""
    from cyberAI.planning import run_test_planner
    
    run_id = args.run_id or generate_run_id()
    setup_logging(run_id, "plan")
    
    console.print(Panel("[bold cyan]Starting Test Planning[/bold cyan]", title="CyberAI"))
    
    planner = run_test_planner(run_id=run_id)
    
    results = {
        "phase": "plan",
        "run_id": run_id,
        "test_plans_generated": len(planner._test_plans),
        "categories": list(planner._plans_by_category.keys()),
    }
    
    table = Table(title="Test Plans by Category")
    table.add_column("Category", style="cyan")
    table.add_column("Plans", style="green")
    
    for cat, plans in planner._plans_by_category.items():
        table.add_row(cat, str(len(plans)))
    
    console.print(table)
    console.print("[green]Planning complete![/green]")
    
    return results


async def run_test(args) -> dict:
    """Run testing phase."""
    from cyberAI.testing import run_tests
    
    run_id = args.run_id or generate_run_id()
    setup_logging(run_id, "test")
    
    categories = args.categories.split(",") if args.categories else None
    
    console.print(Panel(
        f"[bold cyan]Starting Security Testing[/bold cyan]\nCategories: {categories or 'all'}",
        title="CyberAI"
    ))
    
    runner = await run_tests(
        categories=categories,
        max_workers=args.workers,
        run_id=run_id,
    )
    
    results = {
        "phase": "test",
        "run_id": run_id,
        "tests_run": runner._stats["tests_run"],
        "findings_discovered": runner._stats["findings_discovered"],
    }
    
    console.print("[green]Testing complete![/green]")
    return results


async def run_verify(args) -> dict:
    """Run verification phase."""
    from cyberAI.verification import run_verification
    
    run_id = args.run_id or generate_run_id()
    setup_logging(run_id, "verify")
    
    console.print(Panel("[bold cyan]Starting Verification[/bold cyan]", title="CyberAI"))
    
    pipeline = await run_verification(run_id=run_id)
    
    confirmed = pipeline.get_confirmed_findings()
    
    results = {
        "phase": "verify",
        "run_id": run_id,
        "findings_verified": len(pipeline._verified),
        "confirmed": len(confirmed),
    }
    
    console.print(f"[green]Verification complete! {len(confirmed)} findings confirmed.[/green]")
    return results


async def run_report(args) -> dict:
    """Run reporting phase."""
    from cyberAI.reporting import run_report_generation
    
    run_id = args.run_id or generate_run_id()
    setup_logging(run_id, "report")
    
    console.print(Panel("[bold cyan]Generating Reports[/bold cyan]", title="CyberAI"))
    
    generator = await run_report_generation(run_id=run_id)
    outputs = generator.save_all_outputs()
    
    results = {
        "phase": "report",
        "run_id": run_id,
        "reports_generated": len(outputs),
        "output_files": outputs,
    }
    
    table = Table(title="Generated Reports")
    table.add_column("Report", style="cyan")
    table.add_column("Path", style="green")
    
    for name, path in outputs.items():
        table.add_row(name, path)
    
    console.print(table)
    console.print("[green]Reporting complete![/green]")
    
    return results


async def run_full(args) -> dict:
    """Run full assessment (all phases)."""
    run_id = generate_run_id()
    args.run_id = run_id
    
    console.print(Panel(
        f"[bold cyan]Starting Full Security Assessment[/bold cyan]\n"
        f"Target: {args.target}\n"
        f"Run ID: {run_id}",
        title="CyberAI"
    ))
    
    start_time = datetime.utcnow()
    all_results = {"run_id": run_id, "target": args.target, "phases": {}}
    
    try:
        console.print("\n[bold]Phase 1: Reconnaissance[/bold]")
        all_results["phases"]["recon"] = await run_recon(args)
        
        console.print("\n[bold]Phase 2: Planning[/bold]")
        all_results["phases"]["plan"] = await run_plan(args)
        
        console.print("\n[bold]Phase 3: Testing[/bold]")
        all_results["phases"]["test"] = await run_test(args)
        
        console.print("\n[bold]Phase 4: Verification[/bold]")
        all_results["phases"]["verify"] = await run_verify(args)
        
        console.print("\n[bold]Phase 5: Reporting[/bold]")
        all_results["phases"]["report"] = await run_report(args)
        
    finally:
        await cleanup_browser_pool()
        await cleanup_http_client()
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    all_results["duration_seconds"] = duration
    all_results["completed_at"] = end_time.isoformat()
    
    print_final_dashboard(all_results)
    
    return all_results


def print_final_dashboard(results: dict) -> None:
    """Print final assessment dashboard."""
    console.print("\n")
    console.print(Panel("[bold green]Assessment Complete[/bold green]", title="CyberAI"))
    
    table = Table(title="Phase Summary")
    table.add_column("Phase", style="cyan")
    table.add_column("Duration", style="yellow")
    table.add_column("Key Metrics", style="green")
    
    phases = results.get("phases", {})
    
    if "recon" in phases:
        table.add_row("Recon", "-", f"{phases['recon'].get('routes_discovered', 0)} routes")
    
    if "plan" in phases:
        table.add_row("Plan", "-", f"{phases['plan'].get('test_plans_generated', 0)} test plans")
    
    if "test" in phases:
        table.add_row("Test", "-", f"{phases['test'].get('findings_discovered', 0)} findings")
    
    if "verify" in phases:
        table.add_row("Verify", "-", f"{phases['verify'].get('confirmed', 0)} confirmed")
    
    if "report" in phases:
        table.add_row("Report", "-", f"{phases['report'].get('reports_generated', 0)} reports")
    
    console.print(table)
    
    total_findings = phases.get("test", {}).get("findings_discovered", 0)
    confirmed = phases.get("verify", {}).get("confirmed", 0)
    
    findings_table = Table(title="Findings Summary")
    findings_table.add_column("Metric", style="cyan")
    findings_table.add_column("Value", style="green")
    
    findings_table.add_row("Total Findings", str(total_findings))
    findings_table.add_row("Confirmed", str(confirmed))
    findings_table.add_row("Duration", f"{results.get('duration_seconds', 0):.1f}s")
    
    console.print(findings_table)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CyberAI - Enterprise Security Assessment Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    recon_parser = subparsers.add_parser("recon", help="Run reconnaissance")
    recon_parser.add_argument("--target", "-t", required=True, help="Target URL")
    recon_parser.add_argument("--role", "-r", help="Comma-separated roles to test")
    recon_parser.add_argument("--proxy", action="store_true", help="Enable proxy rotation")
    recon_parser.add_argument("--run-id", help="Specific run ID")
    
    plan_parser = subparsers.add_parser("plan", help="Generate test plans")
    plan_parser.add_argument("--recon-dir", help="Recon output directory")
    plan_parser.add_argument("--run-id", help="Specific run ID")
    
    test_parser = subparsers.add_parser("test", help="Run security tests")
    test_parser.add_argument("--plan-dir", help="Planning output directory")
    test_parser.add_argument("--categories", "-c", help="Comma-separated categories")
    test_parser.add_argument("--workers", "-w", type=int, default=4, help="Max workers")
    test_parser.add_argument("--run-id", help="Specific run ID")
    
    verify_parser = subparsers.add_parser("verify", help="Verify findings")
    verify_parser.add_argument("--findings-dir", help="Findings directory")
    verify_parser.add_argument("--run-id", help="Specific run ID")
    
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument("--verified-dir", help="Verified findings directory")
    report_parser.add_argument("--run-id", help="Specific run ID")
    
    full_parser = subparsers.add_parser("full", help="Run full assessment")
    full_parser.add_argument("--target", "-t", required=True, help="Target URL")
    full_parser.add_argument("--proxy", action="store_true", help="Enable proxy rotation")
    full_parser.add_argument("--workers", "-w", type=int, default=4, help="Max workers")
    full_parser.add_argument("--categories", "-c", help="Test categories to run")
    full_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    full_parser.add_argument("--ignore-robots", action="store_true", help="Ignore robots.txt")
    
    parser.add_argument("--env", help="Path to .env file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    config = Config.load(Path(args.env) if hasattr(args, 'env') and args.env else None)
    
    if hasattr(args, 'target') and args.target:
        config.target_url = args.target
    
    if hasattr(args, 'proxy') and args.proxy:
        config.proxy_enabled = True
    
    if hasattr(args, 'workers'):
        config.max_workers = args.workers
    
    if hasattr(args, 'dry_run') and args.dry_run:
        config.dry_run = True
    
    if hasattr(args, 'ignore_robots') and args.ignore_robots:
        config.ignore_robots = True
    
    run_id = getattr(args, 'run_id', None) or generate_run_id()
    
    try:
        if args.command == "recon":
            asyncio.run(run_recon(args))
        elif args.command == "plan":
            asyncio.run(run_plan(args))
        elif args.command == "test":
            asyncio.run(run_test(args))
        elif args.command == "verify":
            asyncio.run(run_verify(args))
        elif args.command == "report":
            asyncio.run(run_report(args))
        elif args.command == "full":
            asyncio.run(run_full(args))
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Assessment interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        write_crash_report(e, run_id)
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Unhandled exception")
        sys.exit(1)


if __name__ == "__main__":
    main()
