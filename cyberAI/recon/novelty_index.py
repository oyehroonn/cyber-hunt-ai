"""
ASRTS Novelty Index: track insertion point shapes to prioritize novel endpoints.

When a new (method, url_template, param_names) shape is seen, it is "novel" and
gets higher priority in the crawl frontier.
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from cyberAI.recon.insertion_point_extractor import shape_hash
from cyberAI.utils.helpers import atomic_write_json, load_json


class NoveltyIndex:
    """
    In-memory set of seen shape hashes. Optional persist to JSON for debugging.
    """

    def __init__(self, persist_path: Optional[Path] = None):
        self._seen: set[str] = set()
        self._persist_path = persist_path

    def add(self, shape_hash_val: str) -> bool:
        """Add shape hash. Returns True if it was new."""
        if shape_hash_val in self._seen:
            return False
        self._seen.add(shape_hash_val)
        return True

    def is_novel(self, shape_hash_val: str) -> bool:
        """True if this shape has not been seen before."""
        return shape_hash_val not in self._seen

    def add_from_canonical(self, method: str, url_template: str, param_names: list[str]) -> bool:
        """Compute shape hash and add. Returns True if novel."""
        h = shape_hash(method, url_template, param_names)
        return self.add(h)

    def save(self) -> None:
        """Persist seen hashes to JSON (optional)."""
        if self._persist_path is None:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self._persist_path, {"shape_hashes": list(self._seen)})
        except Exception as e:
            logger.debug(f"Novelty index save: {e}")

    def load(self) -> None:
        """Load from JSON if path exists."""
        if self._persist_path is None or not self._persist_path.is_file():
            return
        try:
            data = load_json(self._persist_path)
            if data and "shape_hashes" in data:
                self._seen = set(data["shape_hashes"])
        except Exception as e:
            logger.debug(f"Novelty index load: {e}")

    def __len__(self) -> int:
        return len(self._seen)
