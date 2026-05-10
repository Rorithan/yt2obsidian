# processors/webpage.py
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from .base import ContentProcessor

class WebpageProcessor(ContentProcessor):
    def process(self) -> Path:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        resp = requests.get(self.url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Clean up
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else "Web Article"

        # Main content (try common article containers)
        article = (soup.find('article') or 
                   soup.find('main') or 
                   soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'post' in x.lower())))

        html_content = str(article) if article else str(soup.body or soup)

        md_content = markdownify(html_content, heading_style="ATX")

        safe_name = self._get_safe_filename(title_text)
        md_path = self.output_dir / f"{safe_name}.md"

        final_md = f"""---
title: "{title_text}"
date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
type: webpage
url: {self.url}
---

# {title_text}

**Source:** [{self.url}]({self.url})

{md_content}
"""
        md_path.write_text(final_md, encoding='utf-8')
        return md_path