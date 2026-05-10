# processors/instagram.py
import yt_dlp
from pathlib import Path
from datetime import datetime
import subprocess
import re
from .base import ContentProcessor


class InstagramProcessor(ContentProcessor):
    def process(self) -> Path:
        try:
            # 1. Get metadata
            ydl_opts_meta = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extractor_args': {'instagram': {'variant': 'ios'}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15'
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
                info = ydl.extract_info(self.url, download=False)

            raw_title = info.get('title') or info.get('description') or "Instagram Post"
            clean_title = self._clean_title_for_filename(raw_title)
            safe_name = self._get_safe_filename(clean_title)
            video_id = info.get('id', 'igpost')
            base_name = f"{safe_name} [{video_id}]"

            md_path = self.output_dir / f"{base_name}.md"
            video_path = self.output_dir / f"{base_name}.mp4"

            # 2. Download video
            print("⬇️  Downloading video...")
            ydl_opts_download = {
                **ydl_opts_meta,
                'skip_download': False,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitlesformat': 'vtt',
                'subtitleslangs': ['en', 'en-US', 'und'],
                'outtmpl': str(self.output_dir / base_name),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                ydl.download([self.url])

            # 3. Transcribe
            print("🎤 Transcribing with Whisper...")
            transcript = self._transcribe_video(video_path)

            # 4. Build markdown
            content = self._build_markdown(info, base_name, f"{base_name}.mp4", transcript, clean_title)
            md_path.write_text(content, encoding='utf-8')

            self._cleanup_temp_files(base_name)

            print(f"✅ Saved: {md_path.name}")
            print(f"    Video: {video_path.name}")
            return md_path

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    def _clean_title_for_filename(self, title: str) -> str:
        """Clean title for filename - remove emojis and weird chars."""
        clean = re.sub(r'[\U00010000-\U0010ffff]', '', title)   # remove emojis
        clean = re.sub(r'[^a-zA-Z0-9\s\-\']', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:120]

    def _build_markdown(self, info: dict, base_name: str, video_filename: str, transcript: str, clean_title: str) -> str:
        timestamp = info.get('timestamp')
        date_link = "[[No Date]]"
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %dth %Y]]")
            except:
                pass

        # === Improved Uploader Logic ===
        display_name = info.get('uploader') or info.get('channel') or "Unknown"
        username = info.get('uploader_id') or info.get('creator') or ""

        # Clean username
        if username:
            username = username.lstrip('@')
            uploader_str = f"{display_name.strip()} (@{username})"
        else:
            uploader_str = display_name.strip()

        caption = (info.get('description') or clean_title or 'No caption available.').strip()

        md = f"""---
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
        return md

    def _transcribe_video(self, video_path: Path) -> str:
        try:
            cmd = [
                "whisper", str(video_path),
                "--model", "base",
                "--language", "en",
                "--output_format", "srt",
                "--verbose", "False"
            ]
            subprocess.run(cmd, capture_output=True, text=True, cwd=self.output_dir, check=True)

            srt_path = video_path.with_suffix(".srt")
            if srt_path.exists():
                transcript = self._parse_srt(srt_path)
                srt_path.unlink()
                return transcript
            return "> Whisper could not generate transcript."
        except FileNotFoundError:
            return "> Whisper not installed.\nRun: pip install -U openai-whisper && brew install ffmpeg"
        except Exception as e:
            return f"> Transcription failed: {str(e)[:100]}"

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

    def _cleanup_temp_files(self, base_name: str):
        for f in self.output_dir.iterdir():
            if f.is_file() and base_name in f.name and f.suffix not in {".md", ".mp4"}:
                try:
                    f.unlink()
                except:
                    pass