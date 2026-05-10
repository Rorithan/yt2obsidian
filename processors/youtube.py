# processors/youtube.py
import yt_dlp
import requests
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor


class YouTubeProcessor(ContentProcessor):
    def process(self) -> Path:
        ydl_opts_info = {'skip_download': True, 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(self.url, download=False)

        title = info.get('title', 'Untitled')
        safe_name = self._get_safe_filename(title)
        md_path = self.output_dir / f"{safe_name}.md"

        # Download subtitles temporarily
        ydl_opts_sub = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'vtt',
            'subtitleslangs': ['en', 'en-US', 'en-GB'],
            'outtmpl': str(self.output_dir / safe_name),
        }

        with yt_dlp.YoutubeDL(ydl_opts_sub) as ydl:
            ydl.download([self.url])

        content = self._build_markdown(info, safe_name)
        md_path.write_text(content, encoding='utf-8')

        self._download_thumbnail(info, safe_name)
        self._cleanup_vtt_files(safe_name)

        return md_path

    def _build_markdown(self, info: dict, safe_name: str) -> str:
        upload_date = info.get('upload_date')
        date_str = datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d') if upload_date else datetime.now().strftime('%Y-%m-%d')

        thumbnail_local = f"{safe_name}_thumbnail.jpg"
        transcript = self._get_timestamped_transcript(safe_name, info.get('id'))

        md = f"""---
title: "{info.get('title', 'Untitled')}"
date: {date_str}
type: youtube
url: {self.url}
uploader: "{info.get('uploader', 'Unknown')}"
duration: {info.get('duration', 0)}s
---

![[{thumbnail_local}]]

**Uploaded by:** {info.get('uploader')} • {date_str}

## Description
{info.get('description', 'No description available.')}

## Links
- [Watch on YouTube]({self.url})

## Transcript
{transcript}
"""
        return md

    # Keep the rest of the functions exactly as they were (they're working great)
    def _get_timestamped_transcript(self, safe_name: str, video_id: str) -> str:
        vtt_files = list(self.output_dir.glob(f"{safe_name}*.vtt"))
        if not vtt_files:
            return "> No transcript available."

        vtt_path = max(vtt_files, key=lambda p: p.stat().st_mtime)

        try:
            raw = vtt_path.read_text(encoding="utf-8", errors="ignore")
            lines = []
            current_time = 0

            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith(("WEBVTT", "Kind:", "Language:")):
                    continue
                if "-->" in line:
                    try:
                        time_str = line.split("-->")[0].strip().split(".")[0]
                        h, m, s = map(int, time_str.split(":")[:3])
                        current_time = h*3600 + m*60 + s
                    except:
                        continue
                    continue

                if line and not line.startswith(("♪", " ")):
                    clean_line = line.replace("♪", "").strip()
                    if clean_line:
                        ts_link = f"[{self._format_timestamp(current_time)}](https://youtu.be/{video_id}&t={current_time}s)"
                        lines.append(f"{ts_link} {clean_line}")

            grouped = []
            for i in range(0, len(lines), 2):
                grouped.append("\n".join(lines[i:i+2]))
            return "\n\n".join(grouped)

        except Exception as e:
            return f"> Could not parse transcript: {e}"

    def _format_timestamp(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _download_thumbnail(self, info: dict, safe_name: str):
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            try:
                resp = requests.get(thumbnail_url, timeout=10)
                if resp.status_code == 200:
                    (self.output_dir / f"{safe_name}_thumbnail.jpg").write_bytes(resp.content)
            except:
                pass

    def _cleanup_vtt_files(self, safe_name: str):
        for vtt in self.output_dir.glob(f"{safe_name}*.vtt"):
            try:
                vtt.unlink()
            except:
                pass