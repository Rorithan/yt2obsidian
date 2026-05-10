# processors/instagram.py
import yt_dlp
from .base import ContentProcessor


class InstagramProcessor(ContentProcessor):
    def process(self) -> Path:
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)

        title = info.get('title') or info.get('description')[:50] or "Instagram Post"
        safe_name = self._get_safe_filename(title)
        md_path = self.output_dir / f"{safe_name}.md"

        content = self._build_markdown(info)
        md_path.write_text(content, encoding='utf-8')
        return md_path

    def _build_markdown(self, info: dict) -> str:
        thumbnail = info.get('thumbnail', '')
        caption = info.get('description') or info.get('title') or 'No caption'

        md = f"""---
title: "Instagram - {info.get('title', 'Post')}"
date: {info.get('upload_date', '')}
type: instagram
url: {self.url}
---

# Instagram Post

**Author:** {info.get('uploader', 'Unknown')}

{caption}

![thumbnail]({thumbnail})

- [View on Instagram]({self.url})
"""
        return md