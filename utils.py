#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path

def safe_filename(title: str, max_len: int = 150) -> str:
    """Convert title to safe macOS filename (keeps spaces)."""
    clean = re.sub(r'[\\/*?:"<>|]', "", title)
    clean = re.sub(r'\s+', " ", clean.strip())
    return clean[:max_len].strip()

def clean_title_for_filename(title: str) -> str:
    """Remove emojis and special chars for Instagram-style filenames."""
    clean = re.sub(r'[\U00010000-\U0010ffff]', '', title)
    clean = re.sub(r'[^a-zA-Z0-9\s\-\']', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:120]