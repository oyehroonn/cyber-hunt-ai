"""
Load engagement configuration from YAML or JSON.

Default paths: outputs/engagement_config.yaml, config/engagement.yaml, engagement_config.yaml
"""

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from cyberAI.governance.schema import EngagementConfig


def load_engagement_config(path: Optional[str] = None) -> Optional[EngagementConfig]:
    """
    Load and validate engagement config from file.

    Args:
        path: Explicit path to YAML or JSON file. If None, tries default locations.

    Returns:
        EngagementConfig if file exists and is valid; None otherwise (platform runs without scope).
    """
    if path:
        candidates = [Path(path)]
    else:
        candidates = [
            Path("outputs/engagement_config.yaml"),
            Path("outputs/engagement_config.json"),
            Path("config/engagement.yaml"),
            Path("config/engagement.json"),
            Path("engagement_config.yaml"),
            Path("engagement_config.json"),
        ]

    for p in candidates:
        if not p.is_file():
            continue
        try:
            raw = p.read_text(encoding="utf-8")
            if p.suffix.lower() in (".json",):
                data = json.loads(raw)
            else:
                try:
                    import yaml
                    data = yaml.safe_load(raw) or {}
                except ImportError:
                    logger.warning("PyYAML not installed; use JSON engagement config or pip install pyyaml")
                    continue
            config = EngagementConfig.model_validate(data)
            logger.info(f"Loaded engagement config from {p} (engagement_id={config.engagement_id})")
            return config
        except Exception as e:
            logger.warning(f"Failed to load engagement config from {p}: {e}")
            continue

    return None
