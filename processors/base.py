# processors/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class ContentProcessor(ABC):
    """Base class for all content processors."""

    def __init__(self, url: str, output_dir: Path):
        self.url = url.strip()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def process(self) -> Path:
        pass

    def _get_safe_filename(self, title: str) -> str:
        """Convert title to safe filename with SPACES (no underscores)."""
        import re
        clean = re.sub(r'[\\/*?:"<>|]', "", title)      # remove bad chars
        clean = re.sub(r'\s+', " ", clean.strip())      # normalize spaces
        return clean[:150]                              # safe length for macOS