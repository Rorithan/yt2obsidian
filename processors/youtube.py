#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import requests
import re
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config


class YouTubeProcessor(ContentProcessor):
    """YouTube processor: metadata + clean captions + thumbnail → single rich Obsidian markdown."""

    def process(self) -> Path:
        try:
            print("📋 Extracting metadata...")
            with yt_dlp.YoutubeDL({
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }) as ydl:
                info = ydl.extract_info(self.url, download=False)

            title = info.get('title', 'Untitled')
            safe_name = self._get_safe_filename(title)
            md_path = Config.OUTPUT_MD / f"{safe_name}.md"

            print("📝 Downloading and processing captions (expert mode)...")
            transcript_content = self._download_and_process_captions(info, safe_name)

            print("🖼️  Downloading thumbnail...")
            self._download_thumbnail(info, safe_name)

            content = self._build_markdown(info, safe_name, transcript_content)
            md_path.write_text(content, encoding='utf-8')

            print(f"✅ YouTube note created → {md_path.name}")
            print(f"    Transcript lines: {len([line for line in transcript_content.splitlines() if line.strip()])}")
            return md_path

        except Exception as e:
            print(f"❌ YouTube error: {e}")
            raise

    def _download_and_process_captions(self, info: dict, safe_name: str) -> str:
        for manual in (True, False):
            subtitle_opts = {
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
                with yt_dlp.YoutubeDL(subtitle_opts) as ydl:
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
        """Ultra-aggressive cleaner for YouTube auto-generated captions."""
        lines: list[str] = []
        current_ts: str | None = None
        seen = set()

        with vtt_path.open(encoding='utf-8', errors='ignore') as f:
            for raw_line in f:
                line = raw_line.strip()

                if '-->' in line:
                    try:
                        start_part = line.split('-->')[0].strip()
                        current_ts = start_part.split('.')[0]
                    except:
                        current_ts = None
                    continue

                if line and current_ts and not line.startswith(('WEBVTT', 'Kind:', 'Language:')):
                    clean_text = (line
                        .replace('&nbsp;', ' ')
                        .replace('<c>', '').replace('</c>', '')
                        .strip())

                    # Remove EVERY common YouTube auto-caption timing artifact
                    clean_text = re.sub(r'\d{2}:\d{2}\.\d{3}>', ' ', clean_text)
                    clean_text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', ' ', clean_text)
                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                    clean_text = re.sub(r'&gt;&gt;', '', clean_text)
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                    # Skip very short fragments and duplicates
                    if (clean_text and 
                        clean_text not in seen and 
                        len(clean_text) > 3 and 
                        not clean_text.startswith('[')):
                        
                        seen.add(clean_text)
                        timestamp_link = f"[[{safe_name}.mp4#{current_ts}|{current_ts}]]"
                        lines.append(f"{timestamp_link} {clean_text}")

        return "\n\n".join(lines) if lines else "No transcript available."

    def _build_markdown(self, info: dict, safe_name: str, transcript_content: str) -> str:
        # Robust date handling
        date_str = info.get('upload_date') or info.get('release_date') or info.get('timestamp')
        date_link = "[[No Date]]"
        if date_str:
            try:
                if str(date_str).isdigit() and len(str(date_str)) > 8:
                    dt = datetime.fromtimestamp(int(date_str))
                else:
                    dt = datetime.strptime(str(date_str)[:8], '%Y%m%d')
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %d %Y]]")
            except:
                pass

        uploader = info.get('uploader', 'Unknown').replace('"', '').strip()
        duration_hms = self._seconds_to_hms(info.get('duration', 0))
        thumbnail_local = f"{safe_name}_thumbnail.jpg"

        description = (info.get('description') or '').strip() or 'No description available.'

        return f"""---
title: "{info.get('title', 'Untitled')}"
date: "{date_link}"
source: "[[youtube]]"
uploader: "[[{uploader}]]"
duration: "{duration_hms}"
url: "{self.url}"
tags: []
---

![[{thumbnail_local}]]

## Description
{description}

## Transcript
{transcript_content}

---

**Watch on YouTube:** {self.url}
"""

    def _seconds_to_hms(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _download_thumbnail(self, info: dict, safe_name: str):
        thumb_url = info.get('thumbnail') or (info.get('thumbnails') or [{}])[-1].get('url')
        if not thumb_url:
            return
        try:
            resp = requests.get(thumb_url, timeout=10)
            if resp.status_code == 200:
                (Config.OUTPUT_IMAGES / f"{safe_name}_thumbnail.jpg").write_bytes(resp.content)
        except Exception:
            pass