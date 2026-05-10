#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import subprocess
import re
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config
from utils import clean_title_for_filename


class InstagramProcessor(ContentProcessor):
    """Processes Instagram posts/reels into rich Obsidian markdown."""

    def process(self) -> Path:
        try:
            # 1. Extract metadata
            meta_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extractor_args': {'instagram': {'variant': 'ios'}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15'
                },
            }

            with yt_dlp.YoutubeDL(meta_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            raw_title = info.get('title') or info.get('description') or "Instagram Post"
            clean_title = clean_title_for_filename(raw_title)
            safe_name = self._get_safe_filename(clean_title)
            video_id = info.get('id', 'igpost')
            base_name = f"{safe_name} [{video_id}]"

            # Paths using Config (user can change these)
            video_path = Config.OUTPUT_VIDEOS / f"{base_name}.mp4"
            md_path = Config.OUTPUT_MD / f"{base_name}.md"

            # 2. Download video
            print("⬇️  Downloading Instagram media...")
            dl_opts = {
                **meta_opts,
                'skip_download': False,
                'outtmpl': str(Config.OUTPUT_VIDEOS / base_name),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'writethumbnail': False,
            }

            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([self.url])

            # 3. Transcribe with Whisper (macOS native friendly)
            print("🎤 Transcribing with Whisper...")
            transcript = self._transcribe_video(video_path)

            # 4. Build rich Markdown
            content = self._build_markdown(info, base_name, f"{base_name}.mp4", transcript, clean_title)
            md_path.write_text(content, encoding='utf-8')

            self._cleanup_temp_files(base_name)

            print(f"✅ Instagram → {md_path.name}")
            print(f"    Video: {video_path.name}")
            return md_path

        except Exception as e:
            print(f"❌ Instagram error: {e}")
            raise

    def _build_markdown(self, info: dict, base_name: str, video_filename: str, transcript: str, clean_title: str) -> str:
        # Date handling
        timestamp = info.get('timestamp')
        date_link = "[[No Date]]"
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %d %Y]]")
            except:
                pass

        # Uploader logic
        display_name = info.get('uploader') or info.get('channel') or "Unknown"
        username = info.get('uploader_id') or info.get('creator') or ""
        if username:
            username = username.lstrip('@')
            uploader_str = f"{display_name.strip()} (@{username})"
        else:
            uploader_str = display_name.strip()

        caption = (info.get('description') or clean_title or 'No caption available.').strip()

        return f"""---
date: "{date_link}"
source: "[[instagram]]"
uploader: "[[{uploader_str}]]"
url: "{self.url}"
tags: []
---

![[{video_filename}]]   <!-- Video embedded from OUTPUT_VIDEOS -->

## Description
{caption}

## Transcript
{transcript or "> No speech detected."}
"""

    def _transcribe_video(self, video_path: Path) -> str:
        try:
            cmd = [
                "whisper", str(video_path),
                "--model", "base",
                "--language", "en",
                "--output_format", "srt",
                "--verbose", "False"
            ]
            subprocess.run(cmd, capture_output=True, text=True, cwd=Config.OUTPUT_VIDEOS, check=True)

            srt_path = video_path.with_suffix(".srt")
            if srt_path.exists():
                transcript = self._parse_srt(srt_path)
                srt_path.unlink(missing_ok=True)
                return transcript
            return "> Whisper could not generate transcript."
        except FileNotFoundError:
            return "> Whisper not installed.\nRun: pip install -U openai-whisper && brew install ffmpeg"
        except Exception as e:
            return f"> Transcription failed: {str(e)[:120]}"

    def _parse_srt(self, srt_path: Path) -> str:
        raw = srt_path.read_text(encoding="utf-8", errors="ignore")
        lines = []
        current_time = ""

        for line in raw.splitlines():
            line = line.strip()
            if "-->" in line:
                try:
                    time_str = line.split("-->")[0].strip().split(",")[0]
                    h, m, s = map(int, time_str.split(":"))
                    current_time = f"{m:02d}:{s:02d}" if h == 0 else f"{h:02d}:{m:02d}:{s:02d}"
                except:
                    continue
                continue

            if line and not line.isdigit() and current_time:
                lines.append(f"[{current_time}] {line}")

        # Group every 2 lines for readability
        grouped = ["\n".join(lines[i:i+2]) for i in range(0, len(lines), 2)]
        return "\n\n".join(grouped) if grouped else "> No speech detected."

    def _cleanup_temp_files(self, base_name: str):
        """Remove temporary files (srt, temp downloads, etc.)"""
        for f in list(Config.OUTPUT_VIDEOS.iterdir()) + list(Config.OUTPUT_MD.iterdir()):
            if f.is_file() and base_name in f.name and f.suffix not in {".md", ".mp4"}:
                try:
                    f.unlink(missing_ok=True)
                except:
                    pass