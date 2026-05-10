#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import requests
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config


class YouTubeProcessor(ContentProcessor):
    """YouTube processor: metadata + expert-preferred captions + thumbnail → single rich Obsidian markdown."""

    def process(self) -> Path:
        try:
            # 1. Metadata extraction
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

            # 2. Download & process captions (expert/manual first)
            print("📝 Downloading and processing captions (expert mode)...")
            transcript_content = self._download_and_process_captions(info, safe_name)

            # 3. Download thumbnail
            print("🖼️  Downloading thumbnail...")
            self._download_thumbnail(info, safe_name)

            # 4. Build final markdown
            content = self._build_markdown(info, safe_name, transcript_content)
            md_path.write_text(content, encoding='utf-8')

            print(f"✅ YouTube note created → {md_path.name}")
            print(f"    Transcript lines: {len([line for line in transcript_content.splitlines() if line.strip()])}")
            return md_path

        except Exception as e:
            print(f"❌ YouTube error: {e}")
            raise

    def _download_and_process_captions(self, info: dict, safe_name: str) -> str:
        """Try manual (expert) subtitles first, then fall back to auto-generated."""
        for manual in (True, False):  # True = manual, False = auto
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

                    # Cleanup raw VTT
                    vtt_path.unlink(missing_ok=True)
                    return transcript

            except Exception as e:
                continue  # try the other mode

        print("    ⚠️  No captions found (manual or auto)")
        return "No transcript available."

    def _process_vtt_for_obsidian(self, vtt_path: Path, safe_name: str) -> str:
        """Robust VTT cleaner that handles both manual and auto-generated YouTube captions."""
        lines: list[str] = []
        current_ts: str | None = None
        seen = set()  # deduplication

        with vtt_path.open(encoding='utf-8', errors='ignore') as f:
            for raw_line in f:
                line = raw_line.strip()

                if '-->' in line:  # timestamp line
                    try:
                        start_part = line.split('-->')[0].strip()
                        current_ts = start_part.split('.')[0]  # HH:MM:SS
                    except:
                        current_ts = None
                    continue

                if line and current_ts and not line.startswith(('WEBVTT', 'Kind:', 'Language:')):
                    # Aggressive cleaning for YouTube auto-captions
                    clean_text = (line
                        .replace('&nbsp;', ' ')
                        .replace('<c>', '')
                        .replace('</c>', '')
                        .replace('<00:', '')   # remove inline timing junk
                        .strip())

                    # Remove any remaining <timestamp> tags
                    import re
                    clean_text = re.sub(r'<[^>]+>', '', clean_text).strip()

                    if clean_text and clean_text not in seen and not clean_text.startswith('['):
                        seen.add(clean_text)
                        timestamp_link = f"[[{safe_name}.mp4#{current_ts}|{current_ts}]]"
                        lines.append(f"{timestamp_link} {clean_text}")

        if not lines:
            return "No transcript available."

        return "\n\n".join(lines)

    def _build_markdown(self, info: dict, safe_name: str, transcript_content: str) -> str:
        upload_date = info.get('upload_date')
        date_link = "[[No Date]]"
        if upload_date:
            try:
                dt = datetime.strptime(upload_date, '%Y%m%d')
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %d %Y]]")
            except:
                pass

        uploader = info.get('uploader', 'Unknown').replace('"', '').strip()
        duration_hms = self._seconds_to_hms(info.get('duration', 0))
        thumbnail_local = f"{safe_name}_thumbnail.jpg"

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
{info.get('description', 'No description available.')}

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