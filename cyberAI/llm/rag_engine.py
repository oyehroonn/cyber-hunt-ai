"""
RAG Engine

Core Retrieval-Augmented Generation engine for security vulnerability analysis.
Combines vector retrieval with local LLM (Ollama) or DeepSeek API generation.
"""

import json
import os
import time
import re
from pathlib import Path
from typing import Optional, Any, Union
from dataclasses import dataclass

import httpx
from rich.console import Console

# Only replace `{identifier}` when `identifier` is a key in the variables dict.
# Leaves `{name}` and JSON `{"key":...}` alone so recon/crawl text cannot break substitution.
_RAG_VAR_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_SIMILARITY_PLACEHOLDERS = frozenset({"similar_reports", "similar_patterns", "similar_confirmed"})

# Load .env from repository root (parent of cyberAI/) so API keys match main app
try:
    from llm.project_env import load_project_dotenv

    load_project_dotenv()
except ImportError:
    pass

from llm.model_selector import ModelSelector, get_model_selector
from llm.project_env import DEFAULT_DEEPSEEK_BASE, DEFAULT_DEEPSEEK_MODEL, get_openai_compatible_llm_config
from llm.vector_store.chroma_store import ChromaStore, SearchResult

console = Console()


@dataclass 
class GenerationConfig:
    """Configuration for LLM generation."""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096
    stop_sequences: list[str] = None


class DeepSeekAPIClient:
    """
    Client for OpenAI-compatible chat APIs (DeepSeek, OpenRouter, etc.).
    Base URL + model come from project root `.env` via `get_openai_compatible_llm_config()`.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_DEEPSEEK_MODEL,
        base_url: str = DEFAULT_DEEPSEEK_BASE,
        extra_headers: Optional[dict[str, str]] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._extra_headers = extra_headers or {}
        self.client = httpx.Client(timeout=300.0)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """Generate text via DeepSeek chat completions API."""
        config = config or GenerationConfig()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
        }
        # deepseek-reasoner ignores temperature/top_p but accepts them
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.top_p is not None:
            payload["top_p"] = config.top_p

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        headers.update(self._extra_headers)

        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        # Prefer final answer; reasoning_content is CoT (optional to include)
        content = message.get("content", "")
        return content.strip() if content else ""

    def is_available(self) -> bool:
        """Check if API key is set and request would likely succeed."""
        return bool(self.api_key)

    def close(self):
        """Close the HTTP client."""
        self.client.close()


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = httpx.Client(timeout=300.0)  # 5 minute timeout for long generations
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 config: Optional[GenerationConfig] = None) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration
            
        Returns:
            Generated text
        """
        config = config or GenerationConfig()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if config.stop_sequences:
            payload["options"]["stop"] = config.stop_sequences
        
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def chat(self, messages: list[dict], config: Optional[GenerationConfig] = None) -> str:
        """
        Chat-style generation using Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            config: Generation configuration
            
        Returns:
            Assistant response
        """
        config = config or GenerationConfig()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
            }
        }
        
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("message", {}).get("content", "")
    
    def is_available(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            return any(self.model in name or name.startswith(self.model.split(":")[0]) 
                      for name in model_names)
        except Exception:
            return False
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


class RAGEngine:
    """
    Core RAG engine for security vulnerability analysis.
    
    Combines:
    - Vector retrieval from ChromaDB
    - LLM generation via OpenAI-compatible API (`.env`: DEEPSEEK_* / OpenRouter) or Ollama
    - Structured prompt templates
    """

    def __init__(self, data_dir: Optional[Path] = None, model_name: Optional[str] = None):
        """
        Initialize the RAG engine.
        
        If `DEEPSEEK_API_KEY` or `OPENROUTER_API_KEY` is set (project root `.env`),
        uses that provider with `DEEPSEEK_BASE_URL` and `DEEPSEEK_MODEL`.
        Otherwise uses local Ollama.
        
        Args:
            data_dir: Path to data directory (default: llm/data)
            model_name: Model name (Ollama model or DEEPSEEK_MODEL override)
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self.prompts_dir = Path(__file__).parent / "prompts"

        _cfg = get_openai_compatible_llm_config()
        self._deepseek_api_key = _cfg.api_key
        self._use_deepseek_api = bool(self._deepseek_api_key)
        self._api_base_url = _cfg.base_url
        self._api_extra_headers = dict(_cfg.extra_headers)

        # Initialize components
        self.chroma_store = ChromaStore(self.data_dir)

        if self._use_deepseek_api:
            chosen = (model_name or _cfg.model or "").strip()
            self.model_name = chosen or DEFAULT_DEEPSEEK_MODEL
        else:
            if model_name:
                self.model_name = model_name
            else:
                selector = get_model_selector()
                self.model_name = selector.selected_model

        self._llm_client: Optional[Union[OllamaClient, DeepSeekAPIClient]] = None
        self._system_prompt: Optional[str] = None

    def _get_llm_client(self) -> Union[OllamaClient, DeepSeekAPIClient]:
        """Get or create LLM client (DeepSeek API or Ollama)."""
        if self._llm_client is None:
            if self._use_deepseek_api:
                self._llm_client = DeepSeekAPIClient(
                    api_key=self._deepseek_api_key,
                    model=self.model_name,
                    base_url=self._api_base_url,
                    extra_headers=self._api_extra_headers,
                )
            else:
                if not self.model_name:
                    raise RuntimeError(
                        "No model available. Set DEEPSEEK_API_KEY (or OPENROUTER_API_KEY) or run: ollama pull deepseek-r1:14b"
                    )
                self._llm_client = OllamaClient(self.model_name)
        return self._llm_client
    
    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from file."""
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt."""
        if self._system_prompt is None:
            self._system_prompt = self._load_prompt("system_prompt")
        return self._system_prompt
    
    @staticmethod
    def _substitute_rag_variables(template: str, variables: dict) -> str:
        """
        Replace `{key}` only when `key` exists in `variables`.
        Other `{...}` sequences (e.g. `{name}` from JSON in recon) are left unchanged.
        """

        def _replace(m: re.Match) -> str:
            key = m.group(1)
            if key not in variables:
                return m.group(0)
            val = variables[key]
            if val is None:
                return ""
            if isinstance(val, dict):
                val = json.dumps(val, indent=2)
            return str(val)

        return _RAG_VAR_PLACEHOLDER_RE.sub(_replace, template)

    def _format_context(self, results: list[SearchResult]) -> str:
        """Format search results as context string."""
        if not results:
            return "No similar vulnerabilities found in knowledge base."
        
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"""
### Similar Vulnerability #{i}
- **Type**: {r.metadata.get('vuln_class', 'Unknown')}
- **Severity**: {r.metadata.get('severity', 'Unknown')}
- **Source**: {r.metadata.get('source', 'Unknown')}

{r.content}
""")
        
        return "\n".join(context_parts)
    
    def _call_llm_with_retry(self, prompt: str, system_prompt: Optional[str] = None,
                             max_retries: int = 3, config: Optional[GenerationConfig] = None) -> str:
        """Call LLM with retry logic and exponential backoff."""
        client = self._get_llm_client()
        
        for attempt in range(max_retries):
            try:
                return client.generate(prompt, system_prompt=system_prompt, config=config)
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    console.print(f"[yellow]Timeout, retrying in {wait}s (attempt {attempt + 1}/{max_retries})[/yellow]")
                    time.sleep(wait)
                else:
                    raise
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (402, 429):
                    console.print(f"[yellow]Payment/rate-limit error ({e.response.status_code}), falling back to Ollama[/yellow]")
                    try:
                        ollama_client = OllamaClient(self.model_name)
                        return ollama_client.generate(prompt, system_prompt=system_prompt, config=config)
                    except Exception as ollama_err:
                        console.print(f"[red]Ollama fallback also failed: {ollama_err}[/red]")
                        return ""
                elif e.response.status_code >= 500 and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    console.print(f"[yellow]Server error, retrying in {wait}s[/yellow]")
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    console.print(f"[yellow]Error: {e}, retrying in {wait}s[/yellow]")
                    time.sleep(wait)
                else:
                    raise
        
        raise RuntimeError("LLM call failed after all retries")
    
    def _parse_json_response(self, response: str) -> Optional[dict]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to find JSON in code block
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find raw JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return None
    
    # Public API
    
    def retrieve_context(self, query: str, n: int = 5, 
                         vuln_class: Optional[str] = None) -> list[str]:
        """
        Retrieve relevant report chunks for a query.
        
        Args:
            query: Search query
            n: Number of results
            vuln_class: Optional filter by vulnerability class
            
        Returns:
            List of relevant context strings
        """
        filter_metadata = {"vuln_class": vuln_class} if vuln_class else None
        results = self.chroma_store.similarity_search(
            query=query,
            n_results=n,
            filter_metadata=filter_metadata,
        )
        return [r.content for r in results]
    
    def generate(self, prompt_template: str, variables: dict, 
                 n_context: int = 5, use_system_prompt: bool = True) -> str:
        """
        Generate response using RAG.
        
        Args:
            prompt_template: Prompt template with {variable} placeholders
            variables: Variables to fill in template
            n_context: Number of context chunks to retrieve
            use_system_prompt: Whether to include system prompt
            
        Returns:
            Generated response
        """
        # Build query from key variables
        query_parts = []
        for key in ["query", "recon_summary", "finding", "object_model"]:
            if key in variables:
                val = variables[key]
                if isinstance(val, dict):
                    val = json.dumps(val, indent=2)
                query_parts.append(str(val)[:500])
        
        query = " ".join(query_parts) or "security vulnerability"
        
        # Retrieve context
        results = self.chroma_store.similarity_search(query, n_results=n_context)
        context = self._format_context(results)
        
        # Add context to variables (all three names for prompt files that use any of them)
        variables = dict(variables)
        variables["similar_reports"] = context
        variables["similar_patterns"] = context
        variables["similar_confirmed"] = context

        had_similarity_placeholder = any(
            f"{{{k}}}" in prompt_template for k in _SIMILARITY_PLACEHOLDERS
        )

        prompt = self._substitute_rag_variables(prompt_template, variables)

        # Prompts built in code (rag_tester, llm_client) omit {similar_*}; append retrieval context.
        if not had_similarity_placeholder and context.strip():
            prompt = (
                f"{prompt.rstrip()}\n\n"
                "--- Retrieved similar vulnerability reports (knowledge base) ---\n"
                f"{context}\n"
                "--- End knowledge base context ---\n"
            )

        # Generate
        system_prompt = self._get_system_prompt() if use_system_prompt else None
        return self._call_llm_with_retry(prompt, system_prompt=system_prompt)
    
    def analyze_recon(self, intel_dict: dict) -> dict:
        """
        Analyze reconnaissance data for vulnerabilities.
        
        Args:
            intel_dict: Dictionary containing recon data
            
        Returns:
            Structured analysis results
        """
        prompt_template = self._load_prompt("analysis_prompt")
        
        # Format recon summary
        if isinstance(intel_dict, dict):
            recon_summary = json.dumps(intel_dict, indent=2)
        else:
            recon_summary = str(intel_dict)
        
        # Retrieve similar vulnerability patterns
        results = self.chroma_store.similarity_search(recon_summary[:1000], n_results=5)
        similar_reports = self._format_context(results)
        
        prompt = prompt_template.format(
            recon_summary=recon_summary,
            similar_reports=similar_reports,
        )
        
        response = self._call_llm_with_retry(prompt, system_prompt=self._get_system_prompt())
        
        # Parse JSON response
        parsed = self._parse_json_response(response)
        if parsed:
            return parsed
        
        # Return raw response if JSON parsing fails
        return {"raw_analysis": response}
    
    def generate_hypotheses(self, object_model: dict, 
                           permission_matrix: dict,
                           workflow_map: Optional[dict] = None) -> list[dict]:
        """
        Generate attack hypotheses from application model.
        
        Args:
            object_model: Application object/entity model
            permission_matrix: Permission/access control matrix
            workflow_map: Optional workflow definitions
            
        Returns:
            List of attack hypothesis dictionaries
        """
        prompt_template = self._load_prompt("hypothesis_prompt")
        
        # Build query for context retrieval
        query = f"access control {json.dumps(list(object_model.keys())[:10])} authorization"
        results = self.chroma_store.similarity_search(query, n_results=5)
        
        prompt = prompt_template.format(
            object_model=json.dumps(object_model, indent=2),
            permission_matrix=json.dumps(permission_matrix, indent=2),
            workflow_map=json.dumps(workflow_map, indent=2) if workflow_map else "Not provided",
            similar_patterns=self._format_context(results),
        )
        
        response = self._call_llm_with_retry(prompt, system_prompt=self._get_system_prompt())
        
        parsed = self._parse_json_response(response)
        if parsed and "hypotheses" in parsed:
            return parsed["hypotheses"]
        elif parsed:
            return [parsed]
        
        return [{"raw_hypotheses": response}]
    
    def verify_finding(self, finding_dict: dict, evidence: dict) -> dict:
        """
        Verify if a candidate finding is a real vulnerability.
        
        Args:
            finding_dict: Finding details
            evidence: Evidence including request/response, before/after state
            
        Returns:
            Verification result with verdict and confidence
        """
        prompt_template = self._load_prompt("verification_prompt")
        
        # Build query for similar confirmed vulns
        vuln_type = finding_dict.get("vuln_class", finding_dict.get("type", "vulnerability"))
        query = f"{vuln_type} confirmed vulnerability"
        results = self.chroma_store.similarity_search(query, n_results=5)
        
        prompt = prompt_template.format(
            finding=json.dumps(finding_dict, indent=2),
            request_response=evidence.get("request_response", "Not provided"),
            before_state=json.dumps(evidence.get("before_state", {}), indent=2),
            after_state=json.dumps(evidence.get("after_state", {}), indent=2),
            similar_confirmed=self._format_context(results),
        )
        
        response = self._call_llm_with_retry(prompt, system_prompt=self._get_system_prompt())
        
        parsed = self._parse_json_response(response)
        if parsed:
            return parsed
        
        return {
            "verdict": "unknown",
            "confidence": 0.0,
            "reasoning": response,
        }
    
    def write_finding_report(self, finding_dict: dict, evidence: Optional[dict] = None) -> str:
        """
        Generate a professional finding report.
        
        Args:
            finding_dict: Finding details
            evidence: Optional evidence details
            
        Returns:
            Markdown report string
        """
        prompt_template = self._load_prompt("report_prompt")
        
        # Get similar reports for style reference
        vuln_type = finding_dict.get("vuln_class", finding_dict.get("type", "vulnerability"))
        query = f"{vuln_type} security report"
        results = self.chroma_store.similarity_search(query, n_results=3)
        
        prompt = prompt_template.format(
            finding=json.dumps(finding_dict, indent=2),
            evidence=json.dumps(evidence, indent=2) if evidence else "See finding details",
            similar_reports=self._format_context(results),
        )
        
        response = self._call_llm_with_retry(prompt, system_prompt=self._get_system_prompt())
        
        return response
    
    def close(self):
        """Clean up resources."""
        if self._llm_client:
            self._llm_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_rag_engine(data_dir: Optional[Path] = None, 
                      model_name: Optional[str] = None) -> RAGEngine:
    """Factory function to create a RAG engine instance."""
    return RAGEngine(data_dir=data_dir, model_name=model_name)


if __name__ == "__main__":
    # Test the RAG engine
    engine = RAGEngine()
    
    # Check if model is available
    if engine.model_name:
        console.print(f"[green]Using model: {engine.model_name}[/green]")
        
        # Test context retrieval
        context = engine.retrieve_context("SQL injection attack", n=3)
        console.print(f"\n[cyan]Retrieved {len(context)} context chunks[/cyan]")
        
        # Test generation (only if model is available)
        client = engine._get_llm_client()
        if client.is_available():
            console.print("\n[cyan]Testing generation...[/cyan]")
            response = engine.generate(
                "Briefly describe common {vuln_type} attack patterns.",
                {"vuln_type": "SQL injection"},
                n_context=2,
            )
            console.print(f"\n[dim]{response[:500]}...[/dim]")
        else:
            console.print("[yellow]Model not available for generation test[/yellow]")
    else:
        console.print("[red]No model available. Run: ollama pull deepseek-r1:14b[/red]")
