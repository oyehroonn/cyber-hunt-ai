# RAG Pipeline for Cybersecurity Testing Platform

A complete Retrieval-Augmented Generation (RAG) pipeline for security vulnerability analysis. This module provides:

- **200+ scraped vulnerability reports** from real-world sources
- **LLM integration** via local Ollama or **DeepSeek API** (no local GPU needed)
- **Vector-based retrieval** using ChromaDB
- **Drop-in replacement** for the main application's LLM interface

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_rag.txt
```

### 2. Choose LLM: DeepSeek API or local Ollama

**Option A: DeepSeek API (recommended if you can't run large models locally)**

1. Get an API key at [platform.deepseek.com](https://platform.deepseek.com).
2. Copy `.env.example` to `.env` in the project root (or create `.env`).
3. Add your key to `.env`:
   ```bash
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
   ```
4. The pipeline will use `deepseek-reasoner` (R1-style) by default. No Ollama needed.

**Option B: Local Ollama**

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama server (keep running)
ollama serve

# In another terminal, pull a model
ollama pull deepseek-r1:14b
```

If both `DEEPSEEK_API_KEY` and Ollama are available, the pipeline prefers the API.

### 3. Run the Pipeline

```bash
# Check system status
python3 cyberAI/llm/pipeline.py status

# Run full pipeline (scrape → process → embed → test)
python3 cyberAI/llm/pipeline.py full

# Or run steps individually:
python3 cyberAI/llm/pipeline.py scrape      # Scrape vulnerability reports
python3 cyberAI/llm/pipeline.py process     # Process and summarize reports
python3 cyberAI/llm/pipeline.py embed       # Embed into vector store
python3 cyberAI/llm/pipeline.py test        # Test retrieval and generation
```

## Architecture

```
cyberAI/llm/
├── __init__.py                 # Package exports
├── llm_client.py               # DROP-IN replacement (main interface)
├── model_selector.py           # Ollama model detection/selection
├── rag_engine.py               # Core RAG: retrieve + generate
├── pipeline.py                 # CLI pipeline runner
│
├── scraper/                    # Report scrapers
│   ├── hackerone_scraper.py    # HackerOne disclosed reports
│   ├── bugcrowd_scraper.py     # Bugcrowd disclosures
│   ├── portswigger_scraper.py  # PortSwigger Web Security Academy
│   ├── github_scraper.py       # GitHub Security Advisories
│   ├── cve_scraper.py          # NVD/MITRE CVE database
│   └── general_scraper.py      # HackTricks, OWASP, etc.
│
├── processor/                  # Report processing
│   ├── summarizer.py           # LLM-powered summarization
│   ├── chunker.py              # Semantic chunking
│   └── deduplicator.py         # Near-duplicate removal
│
├── vector_store/               # Vector storage
│   └── chroma_store.py         # ChromaDB management
│
├── prompts/                    # LLM prompts
│   ├── system_prompt.txt       # Master system prompt
│   ├── analysis_prompt.txt     # Recon analysis
│   ├── hypothesis_prompt.txt   # Attack hypothesis generation
│   ├── verification_prompt.txt # Finding verification
│   └── report_prompt.txt       # Report generation
│
└── data/                       # Data storage
    ├── raw/                    # Raw scraped reports (JSON)
    ├── processed/              # Structured summaries (JSON)
    └── chroma_db/              # Vector store
```

## API Reference

### Drop-in Functions (`llm_client.py`)

These functions are designed to replace the stub in the main application:

```python
from llm import call_llm, summarize_finding, generate_attack_hypothesis, suggest_test_cases

# Basic LLM call with automatic context retrieval
response = call_llm("Explain IDOR vulnerability patterns")

# Summarize a security finding
summary = summarize_finding({
    "title": "IDOR in User API",
    "type": "IDOR",
    "severity": "high",
    "description": "User can access other users' data..."
})

# Generate attack hypotheses from recon data
hypothesis = generate_attack_hypothesis({
    "endpoints": ["/api/users/{id}", "/api/admin"],
    "parameters": ["user_id", "role"],
})

# Suggest test cases based on application model
test_cases = suggest_test_cases(
    object_model={"objects": ["User", "Order", "Payment"]},
    permission_matrix={"roles": ["admin", "user", "guest"]}
)
```

### RAG Engine Direct Access

For more control, use the RAG engine directly:

```python
from llm.rag_engine import RAGEngine

engine = RAGEngine()

# Retrieve similar vulnerabilities
context = engine.retrieve_context("SQL injection", n=5)

# Analyze recon data
analysis = engine.analyze_recon({"endpoints": [...], "params": [...]})

# Generate attack hypotheses
hypotheses = engine.generate_hypotheses(object_model, permission_matrix)

# Verify a finding
verification = engine.verify_finding(finding_dict, evidence)

# Generate a report
report = engine.write_finding_report(finding_dict)
```

## Model Recommendations

### By Available VRAM/RAM

| VRAM | Recommended Model | Command |
|------|-------------------|---------|
| 48GB+ | `deepseek-r1:32b` | `ollama pull deepseek-r1:32b` |
| 24GB+ | `deepseek-r1:32b` | `ollama pull deepseek-r1:32b` |
| 16GB+ | `deepseek-r1:14b` | `ollama pull deepseek-r1:14b` |
| 12GB+ | `deepseek-r1:14b` | `ollama pull deepseek-r1:14b` |
| 8GB+ | `deepseek-r1:8b` | `ollama pull deepseek-r1:8b` |
| 8GB (tight) | `llama3.1:8b` | `ollama pull llama3.1:8b` |
| CPU only | `mistral:7b` | `ollama pull mistral:7b` |

### Model Priority (Auto-Selected)

1. **deepseek-r1:32b** - Best reasoning, best for security analysis
2. **deepseek-r1:14b** - Excellent balance of quality and speed (recommended)
3. **deepseek-r1:8b** - Good reasoning, smaller footprint
4. **llama3.1:8b** - Fast, good general purpose
5. **mistral:7b** - Very fast, decent structured output

### Manual Override

Set the `LLM_MODEL` environment variable:

```bash
export LLM_MODEL=deepseek-r1:14b
python3 cyberAI/llm/pipeline.py status
```

## Data Sources

The pipeline scrapes from:

| Source | Target Count | Content |
|--------|--------------|---------|
| HackerOne | 60 | Disclosed bug bounty reports |
| Bugcrowd | 40 | Disclosed vulnerability reports |
| PortSwigger | 50 | Web Security Academy labs |
| GitHub | 30 | Security Advisories (GHSA) |
| NVD/CVE | 30 | CVE database entries |
| General | 50 | HackTricks, OWASP, blogs |

Total target: **200+ reports**

### Scraping Notes

- All scrapers respect rate limits (1-6 second delays)
- Scrapers are resumable (skip existing files)
- Raw reports saved as JSON in `data/raw/`
- Use `--max-per-source` to limit per-source counts

## Processing Pipeline

### 1. Summarization

Each raw report is processed into a structured format:

```json
{
  "title": "Short descriptive title",
  "vuln_class": "IDOR | SQL Injection | XSS | ...",
  "cwe": "CWE-XXX",
  "severity": "critical | high | medium | low",
  "attack_vector": "Step-by-step exploitation",
  "root_cause": "Technical failure analysis",
  "impact": "Security impact description",
  "remediation": "How to fix",
  "test_hints": ["Testing indicators"],
  "keywords": ["searchable terms"]
}
```

### 2. Chunking

Reports are split into semantic chunks:

- **attack_pattern**: Vulnerability type + attack vector
- **test_hints**: Root cause + testing indicators
- **remediation**: Impact + fix recommendations
- **full_context**: Complete vulnerability context

### 3. Deduplication

Near-duplicate chunks are removed using embedding similarity (threshold: 0.92).

### 4. Embedding

Chunks are embedded using `all-MiniLM-L6-v2` and stored in ChromaDB collections:

- `vuln_reports` - All processed chunks
- `test_hints` - Testing-focused chunks
- `remediation` - Fix-focused chunks

## Hardware Requirements

### Minimum

- **CPU**: 4+ cores
- **RAM**: 16GB
- **Storage**: 2GB for data + models

### Recommended

- **CPU**: 8+ cores
- **RAM**: 32GB
- **GPU**: NVIDIA with 12GB+ VRAM (or Apple Silicon with 16GB+ unified memory)
- **Storage**: 50GB for larger models

### GPU Support

- **NVIDIA**: Automatic CUDA support via Ollama
- **Apple Silicon**: Automatic Metal support via Ollama
- **AMD**: ROCm support (check Ollama docs)

## Environment Variables

Set these in `.env` in the project root (copy from `.env.example`).

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key (use cloud instead of local Ollama) | None |
| `DEEPSEEK_MODEL` | DeepSeek model name | `deepseek-reasoner` |
| `DEEPSEEK_BASE_URL` | API base URL | `https://api.deepseek.com` |
| `LLM_MODEL` | Force specific Ollama model (when not using API) | Auto-detect |
| `NVD_API_KEY` | NVD API key for faster CVE scraping | None |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |

## Troubleshooting

### Ollama not found

```bash
# Check if Ollama is installed
which ollama

# Install if missing
brew install ollama  # macOS
# or
curl -fsSL https://ollama.ai/install.sh | sh  # Linux
```

### Ollama not running

```bash
# Start Ollama server
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### Model not found

```bash
# List available models
ollama list

# Pull recommended model
ollama pull deepseek-r1:14b
```

### Slow scraping

- Some sources (NVD) have strict rate limits
- Use `--max-per-source` to reduce per-source counts
- Scraping is resumable - run again to continue

### Out of memory

- Use a smaller model: `ollama pull mistral:7b`
- Set `LLM_MODEL=mistral:7b`
- For CPU-only: expect slower responses

## Development

### Running Tests

```bash
# Test individual components
python -m llm.model_selector
python -m llm.vector_store.chroma_store
python -m llm.rag_engine

# Test the full client API
python -m llm.llm_client
```

### Adding New Scrapers

1. Create a new file in `cyberAI/llm/scraper/`
2. Inherit from `BaseScraper`
3. Implement `scrape()` method
4. Add to `cyberAI/llm/scraper/__init__.py`
5. Register in `pipeline.py`

### Modifying Prompts

Edit files in `cyberAI/llm/prompts/`:
- `system_prompt.txt` - Core LLM behavior
- `analysis_prompt.txt` - Recon analysis
- `hypothesis_prompt.txt` - Attack hypothesis
- `verification_prompt.txt` - Finding verification
- `report_prompt.txt` - Report generation

## License

This module is part of the Cyber Hunt security testing platform.
