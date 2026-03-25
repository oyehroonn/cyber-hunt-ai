"""
Model Selector for Ollama LLM

Automatically detects available Ollama models and selects the best one
based on capabilities and available system resources.
"""

import os
import subprocess
import json
import shutil
from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class ModelInfo:
    """Information about an LLM model."""
    name: str
    size_gb: float
    min_vram_gb: float
    capability_score: int
    description: str


MODEL_PRIORITY = [
    ModelInfo("deepseek-r1:32b", 20.0, 24.0, 95, "Best reasoning, needs 24GB+ VRAM"),
    ModelInfo("deepseek-r1:14b", 9.0, 12.0, 90, "Excellent reasoning, needs 12GB+ VRAM"),
    ModelInfo("deepseek-r1:8b", 5.0, 8.0, 85, "Good reasoning, needs 8GB+ VRAM"),
    ModelInfo("deepseek-r1:7b", 4.5, 8.0, 83, "Good reasoning, needs 8GB+ VRAM"),
    ModelInfo("llama3.1:70b", 40.0, 48.0, 92, "Very capable, needs 48GB+ VRAM"),
    ModelInfo("llama3.1:8b", 4.7, 8.0, 75, "Fast and capable"),
    ModelInfo("llama3:8b", 4.7, 8.0, 73, "Fast, good general purpose"),
    ModelInfo("mistral:7b", 4.1, 8.0, 70, "Very fast, decent structured output"),
    ModelInfo("qwen2.5:14b", 9.0, 12.0, 82, "Good alternative to DeepSeek"),
    ModelInfo("qwen2.5:7b", 4.5, 8.0, 78, "Fast alternative"),
    ModelInfo("codellama:13b", 7.4, 10.0, 72, "Code-focused"),
    ModelInfo("phi3:14b", 8.0, 10.0, 76, "Microsoft's efficient model"),
]

MODEL_LOOKUP = {m.name: m for m in MODEL_PRIORITY}


class ModelSelector:
    """Selects the best available Ollama model for security analysis."""
    
    def __init__(self):
        self.available_models: list[str] = []
        self.selected_model: Optional[str] = None
        self.vram_available: Optional[float] = None
        
    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed and accessible."""
        return shutil.which("ollama") is not None
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama server is running."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_available_models(self) -> list[str]:
        """Get list of models available in Ollama."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                return []
            
            models = []
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        models.append(model_name)
            
            self.available_models = models
            return models
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
    
    def get_gpu_vram(self) -> Optional[float]:
        """Attempt to detect available GPU VRAM."""
        # Try nvidia-smi for NVIDIA GPUs
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                total_mb = float(result.stdout.strip().split("\n")[0])
                self.vram_available = total_mb / 1024
                return self.vram_available
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        # Try system_profiler for Apple Silicon
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                # Apple Silicon uses unified memory - estimate available
                # Most M1/M2/M3 Macs have 8-128GB unified memory
                # Assume ~60% can be used for ML workloads
                pass
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Try to get system RAM as fallback (for CPU inference)
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
            # For CPU inference, can use ~50% of system RAM
            self.vram_available = ram_gb * 0.5
            return self.vram_available
        except ImportError:
            pass
        
        return None
    
    def select_best_model(self, manual_override: Optional[str] = None) -> Optional[str]:
        """
        Select the best available model based on priority and resources.
        
        Args:
            manual_override: Specific model to use (from LLM_MODEL env var)
            
        Returns:
            Selected model name or None if no suitable model found
        """
        # Check for manual override
        env_model = manual_override or os.environ.get("LLM_MODEL")
        if env_model:
            if env_model in self.available_models:
                self.selected_model = env_model
                return env_model
            # Check if it's a partial match
            for model in self.available_models:
                if env_model in model or model.startswith(env_model):
                    self.selected_model = model
                    return model
            console.print(f"[yellow]Warning: Requested model '{env_model}' not found in Ollama[/yellow]")
        
        # Select best available model from priority list
        for model_info in MODEL_PRIORITY:
            for available in self.available_models:
                # Check exact match or model family match
                if (available == model_info.name or 
                    available.startswith(model_info.name.split(":")[0])):
                    # Check if we have enough VRAM (if known)
                    if self.vram_available and self.vram_available < model_info.min_vram_gb:
                        continue
                    self.selected_model = available
                    return available
        
        # Fallback: just use the first available model
        if self.available_models:
            self.selected_model = self.available_models[0]
            return self.selected_model
        
        return None
    
    def print_setup_guide(self):
        """Print setup instructions when Ollama is not properly configured."""
        guide = """
[bold red]Ollama not detected or not running.[/bold red]

[bold]Setup Instructions:[/bold]

1. [cyan]Install Ollama:[/cyan]
   Visit: https://ollama.ai
   
   macOS:  brew install ollama
   Linux:  curl -fsSL https://ollama.ai/install.sh | sh

2. [cyan]Pull a recommended model:[/cyan]
   ollama pull deepseek-r1:14b    # Best for security analysis (12GB+ VRAM)
   ollama pull deepseek-r1:8b    # Good balance (8GB+ VRAM)
   ollama pull llama3.1:8b        # Faster alternative (8GB+ VRAM)
   ollama pull mistral:7b         # Lightweight option (8GB+ VRAM)

3. [cyan]Start the Ollama server:[/cyan]
   ollama serve

4. [cyan]Verify installation:[/cyan]
   ollama list

[bold]Recommended Models by Hardware:[/bold]
• 48GB+ VRAM: deepseek-r1:32b or llama3.1:70b
• 24GB+ VRAM: deepseek-r1:32b
• 12GB+ VRAM: deepseek-r1:14b (recommended)
• 8GB+ VRAM:  deepseek-r1:8b or llama3.1:8b
• CPU only:   mistral:7b (slower but works)
"""
        console.print(Panel(guide, title="Ollama Setup Required", border_style="red"))
    
    def print_status(self):
        """Print current model selection status."""
        table = Table(title="LLM Model Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Ollama Installed", "✓ Yes" if self.check_ollama_installed() else "✗ No")
        table.add_row("Ollama Running", "✓ Yes" if self.check_ollama_running() else "✗ No")
        table.add_row("Available Models", str(len(self.available_models)))
        table.add_row("Selected Model", self.selected_model or "None")
        
        if self.vram_available:
            table.add_row("Detected VRAM/RAM", f"{self.vram_available:.1f} GB")
        
        console.print(table)
        
        if self.available_models:
            models_table = Table(title="Available Models")
            models_table.add_column("Model", style="cyan")
            models_table.add_column("Selected", style="green")
            models_table.add_column("Info", style="dim")
            
            for model in self.available_models:
                is_selected = "✓" if model == self.selected_model else ""
                info = MODEL_LOOKUP.get(model.split(":")[0] + ":" + model.split(":")[-1], 
                                        ModelInfo(model, 0, 0, 0, "Unknown model"))
                models_table.add_row(model, is_selected, info.description if info else "")
            
            console.print(models_table)
    
    def initialize(self) -> Optional[str]:
        """
        Full initialization: check Ollama, get models, select best.
        
        Returns:
            Selected model name or None if setup required
        """
        if not self.check_ollama_installed():
            self.print_setup_guide()
            return None
        
        if not self.check_ollama_running():
            self.print_setup_guide()
            return None
        
        self.get_available_models()
        if not self.available_models:
            console.print("[yellow]No models found. Pull a model first:[/yellow]")
            console.print("  ollama pull deepseek-r1:14b")
            return None
        
        self.get_gpu_vram()
        return self.select_best_model()


def get_model_selector() -> ModelSelector:
    """Factory function to get initialized model selector."""
    selector = ModelSelector()
    selector.initialize()
    return selector


if __name__ == "__main__":
    selector = ModelSelector()
    model = selector.initialize()
    selector.print_status()
    
    if model:
        console.print(f"\n[green]Ready to use model: {model}[/green]")
    else:
        console.print("\n[red]Setup required before using the RAG pipeline.[/red]")
