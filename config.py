#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).parent.resolve()

class Config:
    # Default output structure (all in one folder)
    OUTPUT_BASE = PROJECT_ROOT / "output"
    
    # You can override these individually
    OUTPUT_MD: Path = OUTPUT_BASE
    OUTPUT_IMAGES: Path = OUTPUT_BASE
    OUTPUT_VIDEOS: Path = OUTPUT_BASE

    @classmethod
    def ensure_dirs(cls) -> None:
        for p in (cls.OUTPUT_MD, cls.OUTPUT_IMAGES, cls.OUTPUT_VIDEOS):
            p.mkdir(parents=True, exist_ok=True)

    @classmethod
    def set_paths(cls, md: Path = None, images: Path = None, videos: Path = None) -> None:
        if md: cls.OUTPUT_MD = Path(md).resolve()
        if images: cls.OUTPUT_IMAGES = Path(images).resolve()
        if videos: cls.OUTPUT_VIDEOS = Path(videos).resolve()
        cls.ensure_dirs()