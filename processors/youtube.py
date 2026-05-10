#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import requests
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config


class YouTubeProcessor(ContentProcessor):
    """Processes YouTube videos → Obsidian markdown with timestamped transcripts."""

    def process(self) -> Path:
        try:
            # 1. Metadata only
            with yt_dlp.YoutubeDL({
                'skip_download': True,
                'quiet': True,
                'no_warnings': True
            }) as ydl:
                info = ydl.extract_info(self.url, download=False)

            title = info.get('title', 'Untitled')
            safe_name = self._get_safe_filename(title)
            md_path = Config.OUTPUT_MD / f"{safe_name}.md"

            # 2. Subtitles only
            print("📝 Downloading subtitles...")
            sub_opts = {
                'quiet': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitlesformat': 'vtt',
                'subtitleslangs': ['en', 'en-US', 'en-GB'],
                'outtmpl': str(Config.OUTPUT_MD / safe_name),
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(sub_opts) as ydl:
                ydl.download([self.url])

            # 3. Optional full video
            if Config.DOWNLOAD_YOUTUBE_VIDEO:
                print("⬇️  Downloading full video...")
                self._download_video(safe_name)

            # 4. Build markdown
            content = self._build_markdown(info, safe_name)
            md_path.write_text(content, encoding='utf-8')

            # 5. Thumbnail
            self._download_thumbnail(info, safe_name)

            # 6. Cleanup
            self._cleanup_vtt_files(safe_name)

            print(f"✅ YouTube → {md_path.name}")
            return md_path

        except Exception as e:
            print(f"❌ YouTube error: {e}")
            raise

    def _build_markdown(self, info: dict, safe_name: str) -> str:
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
        video_embed = f"![[{safe_name}.mp4]]\n" if Config.DOWNLOAD_YOUTUBE_VIDEO else ""

        transcript = self._get_timestamped_transcript(safe_name, info.get('id'))

        return f"""---
title: "{info.get('title', 'Untitled')}"
date: "{date_link}"
source: "[[youtube]]"
uploader: "[[{uploader}]]"
duration: "{duration_hms}"
url: "{self.url}"
tags: []
---

{video_embed}![[{thumbnail_local}]]

## Description
{info.get('description', 'No description available.')}

## Transcript
{transcript}
"""

    def _get_timestamped_transcript(self, safe_name: str, video_id: str) -> str:
        """Clean, robust VTT parser - removes &nbsp;, extra spaces, and artifacts."""
        vtt_files = list(Config.OUTPUT_MD.glob(f"{safe_name}*.vtt"))
        if not vtt_files:
            return "> No transcript available."

        vtt_path = max(vtt_files, key=lambda p: p.stat().st_mtime)

        try:
            raw = vtt_path.read_text(encoding="utf-8", errors="ignore")

            # === Aggressive cleaning ===
            raw = raw.replace('&nbsp;', ' ')
            raw = raw.replace('\u00a0', ' ')   # non-breaking space
            raw = raw.replace('\u200b', '')    # zero-width space

            lines = []
            current_time = 0

            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "00:", "1", "2", "3")):
                    continue
                if "-->" in line:                     # Timestamp line
                    try:
                        time_str = line.split("-->")[0].strip().split(".")[0]
                        h, m, s = map(int, time_str.split(":")[:3])
                        current_time = h * 3600 + m * 60 + s
                    except:
                        continue
                    continue

                # Clean spoken text
                clean_line = line.replace("♪", "").strip()
                clean_line = ' '.join(clean_line.split())   # normalize whitespace

                if clean_line and len(clean_line) > 1:
                    ts_link = f"[{self._format_timestamp(current_time)}](https://youtu.be/{video_id}&t={current_time}s)"
                    lines.append(f"{ts_link} {clean_line}")

            # Group every 2 lines for readability
            grouped = ["\n".join(lines[i:i+2]) for i in range(0, len(lines), 2)]
            return "\n\n".join(grouped) if grouped else "> Transcript found but empty."

        except Exception as e:
            return f"> Could not parse transcript."

    # === Rest of your methods (unchanged) ===
    def _format_timestamp(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _seconds_to_hms(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _download_video(self, safe_name: str):
        dl_opts = {
            'quiet': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'merge_output_format': 'mp4',
            'outtmpl': str(Config.OUTPUT_VIDEOS / safe_name),
        }
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            ydl.download([self.url])
        print(f"    🎥 Video saved to: {safe_name}.mp4")

    def _download_thumbnail(self, info: dict, safe_name: str):
        thumb_url = info.get('thumbnail')
        if thumb_url:
            try:
                resp = requests.get(thumb_url, timeout=10)
                if resp.status_code == 200:
                    (Config.OUTPUT_IMAGES / f"{safe_name}_thumbnail.jpg").write_bytes(resp.content)
                    print("    📸 Thumbnail saved")
            except:
                print("    ⚠️  Could not download thumbnail")

    def _cleanup_vtt_files(self, safe_name: str):
        for vtt in Config.OUTPUT_MD.glob(f"{safe_name}*.vtt"):
            try:
                vtt.unlink(missing_ok=True)
            except:
                pass
            