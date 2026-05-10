#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.resolve()


class Config:
    """
    Configuration for yt-md.

    HOW TO CHANGE OUTPUT PATHS:
    ===========================
    1. Edit the paths below for permanent changes.
    2. Use command line: python run.py <url> --output ~/Obsidian/Inbox
    """

    # ==================== OUTPUT PATHS ====================
    OUTPUT_BASE = PROJECT_ROOT / "output"

    OUTPUT_MD: Path = OUTPUT_BASE
    OUTPUT_IMAGES: Path = OUTPUT_BASE
    OUTPUT_VIDEOS: Path = OUTPUT_BASE

    # ==================== DOWNLOAD SETTINGS ====================
    DOWNLOAD_YOUTUBE_VIDEO: bool = False

    # ==================== INSTAGRAM SETTINGS ====================
    INSTAGRAM_BROWSER: str = "safari"   # safari, chrome, firefox, edge, etc.

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all output directories."""
        for p in (cls.OUTPUT_MD, cls.OUTPUT_IMAGES, cls.OUTPUT_VIDEOS):
            p.mkdir(parents=True, exist_ok=True)

    @classmethod
    def set_paths(cls, 
                  md: Optional[Path] = None, 
                  images: Optional[Path] = None, 
                  videos: Optional[Path] = None) -> None:
        """Override paths at runtime."""
        if md:      cls.OUTPUT_MD = Path(md).resolve()
        if images:  cls.OUTPUT_IMAGES = Path(images).resolve()
        if videos:  cls.OUTPUT_VIDEOS = Path(videos).resolve()
        cls.ensure_dirs()