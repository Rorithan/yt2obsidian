# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import requests
import re
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config


class YouTubeProcessor(ContentProcessor):
    """YouTube → clean Obsidian markdown (metadata + thumbnail + perfectly cleaned transcript). No video download."""

    def process(self) -> Path:
        try:
            print("📋 Extracting metadata...")
            with yt_dlp.YoutubeDL({'skip_download': True, 'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)

            title = info.get('title', 'Untitled')
            safe_name = self._get_safe_filename(title)
            md_path = Config.OUTPUT_MD / f"{safe_name}.md"

            print("📝 Downloading + cleaning captions (expert mode)...")
            transcript_content = self._download_and_process_captions(info, safe_name)

            print("🖼️  Downloading thumbnail...")
            self._download_thumbnail(info, safe_name)

            content = self._build_markdown(info, safe_name, transcript_content)
            md_path.write_text(content, encoding='utf-8')

            print(f"✅ Created → {md_path.name}")
            return md_path

        except Exception as e:
            print(f"❌ YouTube error: {e}")
            raise

    def _download_and_process_captions(self, info: dict, safe_name: str) -> str:
        for manual in (True, False):  # expert → auto fallback
            opts = {
                'writesubtitles': manual,
                'writeautomaticsub': not manual,
                'subtitleslangs': ['en'],
                'subtitlesformat': 'vtt',
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'outtmpl': str(Config.OUTPUT_MD / safe_name),
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([self.url])

                vtt_files = list(Config.OUTPUT_MD.glob(f"{safe_name}*.vtt"))
                if vtt_files:
                    vtt_path = vtt_files[0]
                    transcript = self._process_vtt_for_obsidian(vtt_path, safe_name)
                    vtt_path.unlink(missing_ok=True)
                    return transcript
            except Exception:
                continue
        print("    ⚠️  No captions found")
        return "No transcript available."

    def _process_vtt_for_obsidian(self, vtt_path: Path, safe_name: str) -> str:
        """Ultra-clean VTT → Obsidian clickable timestamps. Fixed regex + dedup."""
        lines: list[str] = []
        current_ts: str | None = None
        seen = set()

        with vtt_path.open(encoding='utf-8', errors='ignore') as f:
            for raw in f:
                line = raw.strip()

                if '-->' in line:
                    try:
                        start = line.split('-->')[0].strip()
                        current_ts = start.split('.')[0]  # HH:MM:SS
                    except:
                        current_ts = None
                    continue

                if line and current_ts and not line.startswith(('WEBVTT', 'Kind:', 'Language:')):
                    text = (line
                            .replace('&nbsp;', ' ')
                            .replace('<c>', '').replace('</c>', '')
                            .strip())

                    # AGGRESSIVE CLEANING
                    text = re.sub(r'\d{2}:\d{2}\.\d{3}>', ' ', text)
                    text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', ' ', text)
                    text = re.sub(r'<[^>]+>', '', text)
                    text = re.sub(r'>>', '', text)
                    text = re.sub(r'\s+', ' ', text).strip()

                    if (text and text not in seen and len(text) > 4
                            and not text.startswith('[')
                            and not any(x in text.lower() for x in ['00:00', 'stay back'])):
                        seen.add(text)
                        link = f"[[{safe_name}.mp4#{current_ts}|{current_ts}]]"
                        lines.append(f"{link} {text}")

        return "\n\n".join(lines) if lines else "No transcript available."

    def _build_markdown(self, info: dict, safe_name: str, transcript: str) -> str:
        # Date (robust fallbacks)
        date_str = info.get('upload_date') or info.get('release_date') or info.get('timestamp')
        date_link = "[[No Date]]"
        if date_str:
            try:
                if isinstance(date_str, (int, str)) and str(date_str).isdigit():
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
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _download_thumbnail(self, info: dict, safe_name: str):
        url = info.get('thumbnail') or (info.get('thumbnails') or [{}])[-1].get('url')
        if not url:
            return
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                (Config.OUTPUT_IMAGES / f"{safe_name}_thumbnail.jpg").write_bytes(r.content)
        except Exception:
            pass
"""