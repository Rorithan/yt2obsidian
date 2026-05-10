# processors/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class ContentProcessor(ABC):
    """Base class for all content processors (YouTube, Instagram, Webpage)."""

    def __init__(self, url: str, output_dir: Path):
        self.url = url.strip()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def process(self) -> Path:
        """Process the URL and return the path to the generated markdown file."""
        pass

    def _get_safe_filename(self, title: str) -> str:
        """Convert title to safe filename."""
        import re
        clean = re.sub(r'[\\/*?:"<>|]', "", title)
        clean = re.sub(r'\s+', "_", clean.strip())
        return clean[:100]  # limit length