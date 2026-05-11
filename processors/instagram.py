#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yt_dlp
import subprocess
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor
from config import Config
from utils import clean_title_for_filename, move_to_final_paths


class InstagramProcessor(ContentProcessor):
    """Instagram reel/post → clean Obsidian markdown + video.
    Uses TEMP_OUTPUT_DIR for staging, then auto-moves to your final folders."""

    def process(self) -> Path:
        try:
            cookies_tuple = (Config.INSTAGRAM_BROWSER, None, None, None)

            common_opts = {
                'quiet': True,
                'no_warnings': True,
                'cookiesfrombrowser': cookies_tuple,
                'extractor_args': {'instagram': {'variant': 'ios'}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15'
                },
            }

            print(f"Using {Config.INSTAGRAM_BROWSER} cookies for Instagram...")

            # Metadata
            with yt_dlp.YoutubeDL({**common_opts, 'skip_download': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)

            raw_title = info.get('title') or info.get('description') or "Instagram Post"
            clean_title = clean_title_for_filename(raw_title)
            safe_name = self._get_safe_filename(clean_title)
            video_id = info.get('id', 'igpost')
            base_name = f"{safe_name} [{video_id}]"

            # Stage everything in TEMP_OUTPUT_DIR first
            video_path = Config.TEMP_OUTPUT_DIR / f"{base_name}.mp4"
            md_path = Config.TEMP_OUTPUT_DIR / f"{base_name}.md"

            # Download video to temp
            print("Downloading Instagram media...")
            dl_opts = {
                **common_opts,
                'skip_download': False,
                'outtmpl': str(Config.TEMP_OUTPUT_DIR / base_name),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([self.url])

            # Transcribe (Whisper – already in your setup)
            print("Transcribing with Whisper...")
            transcript = self._transcribe_video(video_path)

            # Build MD
            content = self._build_markdown(info, base_name, f"{base_name}.mp4", transcript, clean_title)
            md_path.write_text(content, encoding='utf-8')

            # Move to final folders you set in config.py
            move_to_final_paths(base_name)

            print(f"✅ Instagram → {base_name}.md")
            print(f"    Video: {base_name}.mp4")
            return Config.INSTAGRAM_MARKDOWN_DIR / f"{base_name}.md"

        except Exception as e:
            print(f"❌ Instagram error: {e}")
            raise

    def _build_markdown(self, info: dict, base_name: str, video_filename: str, transcript: str, clean_title: str) -> str:
        timestamp = info.get('timestamp')
        date_link = "[[No Date]]"
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %d %Y]]")
            except:
                pass

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

![[{video_filename}]]

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
            subprocess.run(cmd, capture_output=True, text=True, cwd=Config.TEMP_OUTPUT_DIR, check=True)

            srt_path = video_path.with_suffix(".srt")
            if srt_path.exists():
                transcript = self._parse_srt(srt_path)
                srt_path.unlink(missing_ok=True)
                return transcript
            return "> Whisper could not generate transcript."
        except FileNotFoundError:
            return "> Whisper not installed.\nRun: pip install -U openai-whisper && brew install ffmpeg"
        except Exception as e:
            return f"> Transcription failed: {str(e)[:150]}"

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

        grouped = ["\n".join(lines[i:i+2]) for i in range(0, len(lines), 2)]
        return "\n\n".join(grouped) if grouped else "> No speech detected."