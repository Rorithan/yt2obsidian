#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import shutil
from pathlib import Path
from config import Config


def safe_filename(title: str) -> str:
    """Legacy safe filename (used by base.py and YouTubeProcessor)."""
    if not title:
        return "untitled"
    # Remove invalid chars, collapse spaces, limit length
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = re.sub(r'[\s_-]+', ' ', title).strip()
    return title[:200].rstrip('.')


def clean_title_for_filename(title: str) -> str:
    """New, cleaner version used by InstagramProcessor."""
    if not title:
        return "instagram_post"
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[\s_-]+', ' ', title).strip()
    return title[:100]


def move_to_final_paths(base_name: str, is_youtube: bool = False) -> None:
    """Move markdown + media from TEMP_OUTPUT_DIR to the final paths you set in config.py.
    Called automatically after every successful process()."""
    final = Config.get_final_paths()
    temp = Config.TEMP_OUTPUT_DIR

    if is_youtube:
        # YouTube already writes directly to final paths (legacy-compatible)
        return

    # Instagram flow
    md_source = temp / f"{base_name}.md"
    video_source = temp / f"{base_name}.mp4"

    if md_source.exists():
        shutil.move(str(md_source), str(final["instagram_md"] / md_source.name))
    if video_source.exists():
        shutil.move(str(video_source), str(final["instagram_video"] / video_source.name))

    # Clean up any leftover temp files
    for f in list(temp.iterdir()):
        if base_name in f.name and f.suffix not in {".md", ".mp4"}:
            f.unlink(missing_ok=True)


def get_safe_filename(title: str) -> str:
    """Public helper so _get_safe_filename in base.py still works."""
    return safe_filename(title)