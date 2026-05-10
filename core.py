#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from processors.youtube import YouTubeProcessor
from processors.instagram import InstagramProcessor
# from processors.webpage import WebpageProcessor  # TODO: add later

def get_processor(url: str, force_type: str = "auto"):
    url_lower = url.lower()

    if force_type == "youtube" or any(x in url_lower for x in ["youtube.com", "youtu.be"]):
        return YouTubeProcessor(url)
    elif force_type == "instagram" or "instagram.com" in url_lower:
        return InstagramProcessor(url)
    else:
        # Auto-detect
        if any(x in url_lower for x in ["youtube.com", "youtu.be"]):
            return YouTubeProcessor(url)
        elif "instagram.com" in url_lower:
            return InstagramProcessor(url)
        else:
            # return WebpageProcessor(url)  # future
            return YouTubeProcessor(url)  # fallback