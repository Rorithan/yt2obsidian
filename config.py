#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Config:
    """
    Central configuration for yt2obsidian.
    All processors write to TEMP_OUTPUT_DIR first, then files are moved
    to the four final paths you set below.
    """

    # ==================== TEMPORARY STAGING ====================
    # (everything is written here first — never edit this)
    TEMP_OUTPUT_DIR: Path = PROJECT_ROOT / "output"

    # ==================== FINAL OUTPUT PATHS ====================
    # ←←← JUST PASTE YOUR DESIRED PATHS HERE →→→
    # ~ expands automatically on macOS. These are created automatically.
    YOUTUBE_MARKDOWN_DIR: Path = Path("~/Documents/Obsidian Vault/YouTube").expanduser()
    YOUTUBE_IMAGE_DIR:    Path = Path("~/Documents/Obsidian Vault/YouTube/Attachments").expanduser()

    INSTAGRAM_MARKDOWN_DIR: Path = Path("~/Documents/Obsidian Vault/Instagram").expanduser()
    INSTAGRAM_VIDEO_DIR:    Path = Path("~/Documents/Obsidian Vault/Instagram/Videos").expanduser()

    # ==================== DOWNLOAD SETTINGS ====================
    DOWNLOAD_YOUTUBE_VIDEO: bool = False      # set True if you want full video + timestamps
    DOWNLOAD_INSTAGRAM_VIDEO: bool = True     # Instagram reels/videos are always useful

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create ALL directories (temp + final). Called automatically."""
        for p in (
            cls.TEMP_OUTPUT_DIR,
            cls.YOUTUBE_MARKDOWN_DIR,
            cls.YOUTUBE_IMAGE_DIR,
            cls.INSTAGRAM_MARKDOWN_DIR,
            cls.INSTAGRAM_VIDEO_DIR,
        ):
            p.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_final_paths(cls) -> dict:
        """Helper for utils/move logic — keeps processors clean."""
        return {
            "youtube_md": cls.YOUTUBE_MARKDOWN_DIR,
            "youtube_img": cls.YOUTUBE_IMAGE_DIR,
            "instagram_md": cls.INSTAGRAM_MARKDOWN_DIR,
            "instagram_video": cls.INSTAGRAM_VIDEO_DIR,
        }

    @classmethod
    def set_temp_dir(cls, path: Optional[Path | str] = None) -> None:
        """CLI --output support (still works exactly as before)."""
        if path:
            cls.TEMP_OUTPUT_DIR = Path(path).resolve()
        cls.ensure_dirs()