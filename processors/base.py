#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
from config import Config
from utils import safe_filename


class ContentProcessor(ABC):
    """Base class for all processors."""

    def __init__(self, url: str, output_dir: Path = None):
        self.url = url.strip()
        self.output_dir = output_dir or Config.OUTPUT_MD
        Config.ensure_dirs()

    @abstractmethod
    def process(self) -> Path:
        """Process URL and return path to created .md file."""
        pass

    def _get_safe_filename(self, title: str) -> str:
        return safe_filename(title)