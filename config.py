#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Config:
    """
    Central configuration for yt2obsidian.
    Processors write directly to the legacy OUTPUT_* paths (for full compatibility
    with current youtube.py + instagram.py). These point to your final folders.
    TEMP_OUTPUT_DIR + move logic is ready for when we update the processors later.
    """

    # ==================== TEMPORARY STAGING ====================
    TEMP_OUTPUT_DIR: Path = PROJECT_ROOT / "output"

    # ==================== FINAL OUTPUT PATHS ====================
    # ←←← JUST PASTE YOUR DESIRED PATHS HERE →→→
    # ~ expands automatically. Folders are created automatically.
    YOUTUBE_MARKDOWN_DIR: Path = Path("/Users/rorymcknightiii/Library/Mobile Documents/iCloud~md~obsidian/Documents/rory-brain/utilities/data-repo/youtube").expanduser()
    YOUTUBE_IMAGE_DIR:    Path = Path("/Users/rorymcknightiii/Library/Mobile Documents/iCloud~md~obsidian/Documents/rory-brain/utilities/images").expanduser()

    INSTAGRAM_MARKDOWN_DIR: Path = Path("/Users/rorymcknightiii/Library/Mobile Documents/iCloud~md~obsidian/Documents/rory-brain/utilities/data-repo/reels-tiktok").expanduser()
    INSTAGRAM_VIDEO_DIR:    Path = Path("/Users/rorymcknightiii/Library/Mobile Documents/iCloud~md~obsidian/Documents/rory-brain/utilities/videos").expanduser()

    # ==================== LEGACY COMPATIBILITY (current processors) ====================
    # These point to the final paths you set above so nothing breaks.
    # Instagram markdown will currently land in YOUTUBE_MARKDOWN_DIR (easy to change later).
    OUTPUT_MD:     Path = YOUTUBE_MARKDOWN_DIR
    OUTPUT_IMAGES: Path = YOUTUBE_IMAGE_DIR
    OUTPUT_VIDEOS: Path = INSTAGRAM_VIDEO_DIR

    # ==================== DOWNLOAD SETTINGS ====================
    DOWNLOAD_YOUTUBE_VIDEO: bool = False
    DOWNLOAD_INSTAGRAM_VIDEO: bool = True

    # Instagram needs browser cookies (yt-dlp built-in, no extra deps)
    INSTAGRAM_BROWSER: str = "chrome"   # Options: "chrome", "safari", "firefox", "edge"
                                         # → Must be logged into Instagram in that browser

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all directories automatically."""
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
        """Future-proof helper (used by utils/move logic once processors are updated)."""
        return {
            "youtube_md": cls.YOUTUBE_MARKDOWN_DIR,
            "youtube_img": cls.YOUTUBE_IMAGE_DIR,
            "instagram_md": cls.INSTAGRAM_MARKDOWN_DIR,
            "instagram_video": cls.INSTAGRAM_VIDEO_DIR,
        }

    @classmethod
    def set_temp_dir(cls, path: Optional[Path | str] = None) -> None:
        """CLI --output support."""
        if path:
            cls.TEMP_OUTPUT_DIR = Path(path).resolve()
        cls.ensure_dirs()