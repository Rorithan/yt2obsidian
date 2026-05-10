# processors/youtube.py
import yt_dlp
import requests
from pathlib import Path
from datetime import datetime
from .base import ContentProcessor


class YouTubeProcessor(ContentProcessor):
    def process(self) -> Path:
        try:
            ydl_opts_info = {'skip_download': True, 'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(self.url, download=False)

            title = info.get('title', 'Untitled')
            safe_name = self._get_safe_filename(title)
            md_path = self.output_dir / f"{safe_name}.md"

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

            print(f"✅ Created: {md_path.name}")
            return md_path

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    def _build_markdown(self, info: dict, safe_name: str) -> str:
        upload_date = info.get('upload_date')
        if upload_date:
            try:
                dt = datetime.strptime(upload_date, '%Y%m%d')
                date_link = dt.strftime("[[journal/%Y/%m %B/%B %d %Y|%B %dth %Y]]")
            except:
                date_link = "[[No Date]]"
        else:
            date_link = "[[No Date]]"

        uploader = info.get('uploader', 'Unknown').replace('"', '').strip()
        duration_hms = self._seconds_to_hms(info.get('duration', 0))

        thumbnail_local = f"{safe_name}_thumbnail.jpg"
        transcript = self._get_timestamped_transcript(safe_name, info.get('id'))

        md = f"""---
title: "{info.get('title', 'Untitled')}"
date: "{date_link}"
source: "[[youtube]]"
uploader: "[[{uploader}]]"
duration: "{duration_hms}"
tags: []
---

![[{thumbnail_local}]]

## Description
{info.get('description', 'No description available.')}

## Transcript
{transcript}
"""
        return md

    # ... (keep all the other methods exactly the same: _seconds_to_hms, _get_timestamped_transcript, etc.)