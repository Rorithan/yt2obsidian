#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import requests
import re
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config


def _extract_video_id(url: str) -> str | None:
    """Robust YouTube ID extraction (stdlib only)."""
    if not url:
        return None
    # youtu.be short links
    match = re.search(r'youtu\.be/([0-9A-Za-z_-]{11})', url)
    if match:
        return match.group(1)
    # youtube.com/watch?v=...
    parsed = urlparse(url) if 'urlparse' in globals() else None  # fallback safety
    if parsed and ("youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc):
        from urllib.parse import parse_qs
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]
    # fallback regex for any YouTube URL
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None


def _timestamp_to_seconds(timestamp: str) -> int:
    """HH:MM:SS, MM:SS or SS → total seconds (used for YouTube &t= link)."""
    timestamp = re.sub(r"[^\d:]", "", timestamp.strip())
    parts = [int(p) for p in timestamp.split(":") if p]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 1:
        return parts[0]
    return 0


def _format_youtube_timestamp_link(timestamp: str, video_id: str) -> str:
    """EXACT format you requested:
    [00:03:51](https://www.youtube.com/watch?v=7dmLRWSvLDo&t=231s)"""
    seconds = _timestamp_to_seconds(timestamp)
    url = f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"
    return f"[{timestamp}]({url})"


class YouTubeProcessor(ContentProcessor):
    """YouTube → clean Obsidian markdown (metadata + thumbnail + perfectly cleaned transcript).
    No video download by default (respects Config.DOWNLOAD_YOUTUBE_VIDEO)."""

    def process(self) -> Path:
        try:
            print("Extracting metadata...")
            with yt_dlp.YoutubeDL({'skip_download': True, 'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)

            title = info.get('title', 'Untitled')
            # Extra sanitization to prevent double periods and weird filenames
            safe_name = self._get_safe_filename(title).rstrip('.').rstrip()

            md_path = Config.OUTPUT_MD / f"{safe_name}.md"

            # NEW: extract video ID once (used for the new timestamp links)
            video_id = info.get('id') or _extract_video_id(self.url)
            if not video_id:
                raise ValueError(f"Could not extract video ID from {self.url}")

            print("Processing captions...")
            transcript = self._download_and_process_captions(info, safe_name, video_id)

            print("Thumbnail...")
            self._download_thumbnail(info, safe_name)

            content = self._build_markdown(info, safe_name, transcript)
            md_path.write_text(content, encoding='utf-8')

            print(f"✅ {md_path.name}")
            return md_path

        except Exception as e:
            print(f"❌ YouTube error: {e}")
            raise

    def _download_and_process_captions(self, info: dict, safe_name: str, video_id: str) -> str:
        """Download subtitles (manual preferred → auto fallback) and clean.
        (Only change: now passes video_id down for new timestamp format)"""
        for manual in (True, False):
            opts = {
                'writesubtitles': manual,
                'writeautomaticsub': not manual,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'vtt',
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'outtmpl': str(Config.TEMP_OUTPUT_DIR / safe_name),  # use temp staging
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([self.url])

                vtt_files = list(Config.TEMP_OUTPUT_DIR.glob(f"{safe_name}*.vtt"))
                if vtt_files:
                    vtt_path = vtt_files[0]
                    transcript = self._process_vtt_for_obsidian(vtt_path, safe_name, video_id)
                    vtt_path.unlink(missing_ok=True)
                    return transcript
            except Exception:
                continue
        print("    No captions found")
        return "No transcript available."

    def _process_vtt_for_obsidian(self, vtt_path: Path, safe_name: str, video_id: str) -> str:
        """Ultra-clean VTT parser — now uses the exact YouTube timestamp link format you asked for.
        (Everything else — cleaning logic, duplicate removal, etc. — is untouched)."""
        lines: list[str] = []
        current_ts: str | None = None
        last_text: str = ""

        with vtt_path.open(encoding='utf-8', errors='ignore') as f:
            for raw in f:
                line = raw.strip()

                # Extract timestamp from cue line
                if '-->' in line:
                    try:
                        start = line.split('-->')[0].strip()
                        # Convert to Obsidian-friendly HH:MM:SS
                        current_ts = start.split('.')[0] if '.' in start else start
                    except Exception:
                        current_ts = None
                    continue

                if not line or line.startswith(('WEBVTT', 'Kind:', 'Language:')):
                    continue

                # Aggressive cleaning for YouTube's messy caption format (unchanged)
                text = line
                text = re.sub(r'<[^>]+>', '', text)                    # remove all HTML/caption tags
                text = re.sub(r'<\d{2}:\d{2}:\d{2}>', '', text)        # <00:00:01>
                text = re.sub(r'<\d{2}:\d{2}>', '', text)              # <00:01>
                text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}', '', text)   # 00:00:01.000
                text = re.sub(r'\d{2}:\d{2}', '', text)                # leftover MM:SS
                text = re.sub(r'&nbsp;', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()

                if not text or len(text) < 5 or text == last_text:
                    continue

                last_text = text

                if current_ts:
                    # NEW: exactly the format you requested (replaces the old local [[mp4]] link)
                    linked_ts = _format_youtube_timestamp_link(current_ts, video_id)
                    lines.append(f"{linked_ts} {text}")

        return "\n\n".join(lines) if lines else "No transcript available."

    def _build_markdown(self, info: dict, safe_name: str, transcript: str) -> str:
        """Build rich Obsidian markdown. (100% unchanged from your last working version)"""
        # Robust date parsing
        date_str = info.get('upload_date') or info.get('release_date') or info.get('timestamp')
        date_link = "[[No Date]]"
        if date_str:
            try:
                if str(date_str).isdigit() and len(str(date_str)) == 10:  # unix timestamp
                    dt = datetime.fromtimestamp(int(date_str))
                else:
                    dt = datetime.strptime(str(date_str)[:8], '%Y%m%d')
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %d %Y]]")
            except Exception:
                pass

        uploader = info.get('uploader', 'Unknown').replace('"', '').strip()
        duration = self._seconds_to_hms(info.get('duration', 0))
        desc = (info.get('description') or '').strip() or 'No description available.'

        return f"""---
title: "{info.get('title', 'Untitled')}"
date: "{date_link}"
source: "[[youtube]]"
uploader: "[[{uploader}]]"
duration: "{duration}"
url: "{self.url}"
tags: []
---

![[{safe_name}_thumbnail.jpg]]

## Description
{desc}

## Transcript
{transcript}

---

**Watch on YouTube:** {self.url}
"""

    def _seconds_to_hms(self, seconds: int) -> str:
        """Convert seconds to HH:MM:SS or MM:SS. (unchanged)"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _download_thumbnail(self, info: dict, safe_name: str):
        """Download thumbnail. (unchanged)"""
        url = info.get('thumbnail') or (info.get('thumbnails') or [{}])[-1].get('url')
        if not url:
            return
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                (Config.OUTPUT_IMAGES / f"{safe_name}_thumbnail.jpg").write_bytes(r.content)
        except Exception:
            pass