"""
Configuration management for CyberAI platform.
Loads settings from environment variables and .env file.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class RoleAccount:
    """Represents a role account for testing."""
    role: str
    username: str
    password: str
    mfa_secret: Optional[str] = None


@dataclass
class Config:
    """
    Global configuration singleton for the CyberAI platform.
    All settings are loaded from environment variables.
    """
    # Target configuration
    target_url: str = ""
    
    # Proxy settings
    proxy_enabled: bool = False
    proxy_source_url: str = "https://free-proxy-list.net/"
    proxy_cache_ttl_minutes: int = 30
    
    # Captcha settings
    captcha_api_key: str = ""
    captcha_service: str = "2captcha"  # 2captcha, anticaptcha
    
    # Browser settings
    headless: bool = True
    browser_timeout_ms: int = 30000
    user_agent_rotation: bool = True
    
    # Execution settings
    max_workers: int = 4
    request_delay_ms: int = 200
    max_requests_per_endpoint: int = 10
    rate_limit_window_seconds: int = 10
    
    # LLM settings
    llm_enabled: bool = False
    # Structured LLM orchestration (phase context + final markdown report)
    llm_orchestration_enabled: bool = True
    # Confirmatory tests: differential auth + unauth vs auth + OOB SSRF (any target)
    confirmed_tests_enabled: bool = True
    # JSON string: registration API spec for automated test users (see .env.example)
    auto_register_spec: str = ""
    # Out-of-band SSRF: webhook.site inbox UUID (optional)
    webhook_site_uuid: str = ""
    # Seconds to poll OOB callback
    oob_poll_timeout_seconds: float = 35.0

    # Closed-loop agent (see docs/AGENT_LOOP_ARCHITECTURE.md)
    agent_max_turns: int = 50
    agent_log_tail_lines: int = 80
    
    # Role accounts for multi-role testing
    role_accounts: list[RoleAccount] = field(default_factory=list)
    
    # Paths
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    
    # Run configuration
    run_id: str = ""
    ignore_robots: bool = False
    dry_run: bool = False

    # ASRTS engagement config (optional): path to YAML/JSON for scope and rate limits
    engagement_config_path: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    verbose: bool = False
    
    _instance: Optional["Config"] = field(default=None, repr=False, init=False)
    
    def __post_init__(self):
        """Ensure output directories exist."""
        self._ensure_output_dirs()
    
    def _ensure_output_dirs(self) -> None:
        """Create all required output directories."""
        subdirs = [
            "llm/engagement",
            "llm/agent_memory",
            "recon/screenshots",
            "recon/dom_snapshots", 
            "recon/requests",
            "recon/js_bundles",
            "recon/intelligence",
            "planning",
            "testing/findings",
            "verification/confirmed",
            "reports/markdown",
            "reports/json",
            "reports/csv",
            "reports/txt",
            "logs",
            "warc",  # ASRTS: WARC evidence store
            "sessions",  # ASRTS: session store (file-backed)
        ]
        for subdir in subdirs:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load(cls, env_path: Optional[Path] = None) -> "Config":
        """
        Load configuration from environment variables.
        
        Args:
            env_path: Optional path to .env file
            
        Returns:
            Configured Config instance
        """
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        role_accounts = []
        role_accounts_json = os.getenv("ROLE_ACCOUNTS", "[]")
        try:
            accounts_data = json.loads(role_accounts_json)
            for acc in accounts_data:
                role_accounts.append(RoleAccount(
                    role=acc.get("role", "user"),
                    username=acc.get("username", ""),
                    password=acc.get("password", ""),
                    mfa_secret=acc.get("mfa_secret"),
                ))
        except json.JSONDecodeError:
            pass
        
        config = cls(
            target_url=os.getenv("TARGET_URL", ""),
            proxy_enabled=os.getenv("PROXY_ENABLED", "false").lower() == "true",
            proxy_source_url=os.getenv("PROXY_SOURCE_URL", "https://free-proxy-list.net/"),
            proxy_cache_ttl_minutes=int(os.getenv("PROXY_CACHE_TTL_MINUTES", "30")),
            captcha_api_key=os.getenv("CAPTCHA_API_KEY", ""),
            captcha_service=os.getenv("CAPTCHA_SERVICE", "2captcha"),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            browser_timeout_ms=int(os.getenv("BROWSER_TIMEOUT_MS", "30000")),
            user_agent_rotation=os.getenv("USER_AGENT_ROTATION", "true").lower() == "true",
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            request_delay_ms=int(os.getenv("REQUEST_DELAY_MS", "200")),
            max_requests_per_endpoint=int(os.getenv("MAX_REQUESTS_PER_ENDPOINT", "10")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "10")),
            llm_enabled=os.getenv("LLM_ENABLED", "false").lower() == "true",
            llm_orchestration_enabled=os.getenv("LLM_ORCHESTRATION", "true").lower() == "true",
            confirmed_tests_enabled=os.getenv("CONFIRMED_TESTS_ENABLED", "true").lower() == "true",
            auto_register_spec=os.getenv("AUTO_REGISTER_SPEC", "").strip(),
            webhook_site_uuid=os.getenv("WEBHOOK_SITE_UUID", "").strip(),
            oob_poll_timeout_seconds=float(os.getenv("OOB_POLL_TIMEOUT_SECONDS", "35")),
            agent_max_turns=int(os.getenv("AGENT_MAX_TURNS", "50")),
            agent_log_tail_lines=int(os.getenv("AGENT_LOG_TAIL_LINES", "80")),
            role_accounts=role_accounts,
            output_dir=Path(os.getenv("OUTPUT_DIR", "outputs")),
            ignore_robots=os.getenv("IGNORE_ROBOTS", "false").lower() == "true",
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            engagement_config_path=os.getenv("ENGAGEMENT_CONFIG_PATH") or None,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            verbose=os.getenv("VERBOSE", "false").lower() == "true",
        )
        
        cls._instance = config
        return config
    
    @classmethod
    def get(cls) -> "Config":
        """Get the current configuration instance."""
        if cls._instance is None:
            cls._instance = cls.load()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the configuration singleton."""
        cls._instance = None
    
    def get_role_account(self, role: str) -> Optional[RoleAccount]:
        """Get account credentials for a specific role."""
        for account in self.role_accounts:
            if account.role == role:
                return account
        return None
    
    def get_output_path(self, *parts: str) -> Path:
        """Get a path within the output directory."""
        return self.output_dir.joinpath(*parts)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "target_url": self.target_url,
            "proxy_enabled": self.proxy_enabled,
            "headless": self.headless,
            "max_workers": self.max_workers,
            "request_delay_ms": self.request_delay_ms,
            "llm_enabled": self.llm_enabled,
            "output_dir": str(self.output_dir),
            "roles_configured": [acc.role for acc in self.role_accounts],
        }


def get_config() -> Config:
    """Convenience function to get the current configuration."""
    return Config.get()


if __name__ == "__main__":
    import sys
    
    config = Config.load()
    print("Loaded configuration:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
