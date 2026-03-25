# CyberAI

Enterprise-grade AI-powered cybersecurity reconnaissance and vulnerability testing platform.

## Overview

CyberAI is a multi-phase, multi-worker, fully automated security assessment system designed for terminal operation. It performs comprehensive reconnaissance, generates intelligent test plans, executes security tests, verifies findings, and produces detailed reports.

**Key Features:**
- No web UI, no database - everything persists as JSON, CSV, TXT, and Markdown files
- Async-first architecture with parallel test execution
- Multi-role and multi-state testing
- GraphQL and WebSocket vulnerability detection
- Intelligent test planning based on reconnaissance
- Comprehensive reporting with executive summaries and engineering handoffs

## Installation

```bash
# Clone the repository
cd cyberAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
TARGET_URL=https://your-target.com
PROXY_ENABLED=false
HEADLESS=true
MAX_WORKERS=4
LLM_ENABLED=false  # Enable when RAG pipeline is ready

# Role accounts for multi-role testing (JSON array)
ROLE_ACCOUNTS=[{"role": "admin", "username": "admin@example.com", "password": "..."}]
```

## Usage

### Full Assessment

Run all phases sequentially:

```bash
python main.py full --target https://example.com
```

### Individual Phases

```bash
# Phase 1: Reconnaissance
python main.py recon --target https://example.com

# Phase 2: Test Planning
python main.py plan

# Phase 3: Security Testing
python main.py test --categories auth,authz --workers 8

# Phase 4: Finding Verification
python main.py verify

# Phase 5: Report Generation
python main.py report
```

### Options

```bash
python main.py full --target https://example.com \
    --proxy              # Enable proxy rotation
    --workers 8          # Max concurrent workers
    --categories auth,authz,race  # Specific test categories
    --dry-run            # Simulate without real requests
    --ignore-robots      # Ignore robots.txt restrictions
```

## Project Structure

```
cyberAI/
├── main.py                 # Master orchestrator
├── config.py               # Configuration management
├── models.py               # Pydantic data models
├── .env.example            # Environment template
│
├── recon/                  # Steps 1-16: Reconnaissance
│   ├── core_discovery.py   # BFS crawling, screenshots, DOM
│   ├── network_intelligence.py  # Request interception
│   ├── frontend_parser.py  # JS bundle analysis
│   ├── role_discovery.py   # Multi-role comparison
│   └── ...
│
├── planning/               # Step 17: Test Planning
│   └── test_planner.py
│
├── testing/                # Steps 18.1-18.18: Security Tests
│   ├── runner.py           # Parallel test orchestrator
│   ├── auth_testing.py
│   ├── authorization_testing.py
│   └── ...
│
├── verification/           # Steps 19.1-19.12: Verification
│   ├── pipeline.py
│   └── ...
│
├── reporting/              # Steps 20.1-20.10: Reports
│   ├── reporter.py
│   └── templates/
│
├── llm/                    # RAG / LLM (ChromaDB, rag_engine, llm_client)
│
├── utils/                  # Shared utilities
│   ├── browser.py          # Playwright management
│   ├── http_client.py      # httpx wrapper
│   ├── proxy_manager.py    # Proxy rotation
│   └── attack_graph.py     # NetworkX graphs
│
└── outputs/                # All outputs (gitignored)
    ├── recon/
    ├── planning/
    ├── testing/
    ├── verification/
    └── reports/
```

## Output Files

All outputs are written to the `outputs/` directory:

- **JSON**: Structured data with `_meta` headers
- **CSV**: Tabular data via pandas
- **Markdown**: Jinja2-templated reports
- **TXT**: Plain text for executive reading
- **PNG**: Screenshots from browser automation

## Test Categories

| Category | Description |
|----------|-------------|
| `auth` | Authentication testing (login, session, MFA) |
| `authz` | Authorization testing (IDOR, privilege escalation) |
| `business_logic` | Workflow bypass, duplicate submission |
| `input` | Input validation fuzzing |
| `mass_assignment` | Hidden field injection |
| `race` | Race condition testing |
| `graphql` | GraphQL-specific vulnerabilities |
| `websocket` | WebSocket authorization |
| `file_upload` | File type confusion, SSRF |
| `config` | Security header analysis |

## LLM Integration

The system works fully without LLM. To enable LLM-powered analysis:

1. Configure API keys / Ollama in the project root `.env` (see `cyberAI/.env.example`)
2. Set `LLM_ENABLED=true` in `.env`
3. See `llm/README_RAG.md` for the knowledge-base pipeline and dependencies

The LLM enhances:
- Attack hypothesis generation
- Finding summarization
- Remediation advice
- Business impact explanation

## Development

```bash
# Run linter
ruff check .

# Run tests
pytest

# Format code
ruff format .
```

## Security Notice

This tool is designed for authorized security testing only. Always obtain proper authorization before testing any system. The authors are not responsible for misuse.

## License

MIT License - See LICENSE file for details.
