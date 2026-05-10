# yt2obsidian

terminal command for any supported link:
python3 cli.py ""

A lightweight macOS terminal tool that turns YouTube, Instagram, and webpage links into rich Obsidian-ready Markdown files.

## Features
- Auto-detects content type or force with `--type`
- YouTube: title, description, uploader, date, thumbnail embed, subtitles (if available)
- Instagram: post/reel metadata + caption
- Webpages: clean title, main content, metadata
- Safe filenames, YAML frontmatter for Obsidian
- Zero bloat — uses built-ins + minimal dependencies

## Installation (one-time) and dependancies

```bash
brew install yt-dlp
pip install requests beautifulsoup4 markdownify  # only these three

Terminal commands
python3 cli.py "https://youtube.com/watch?v=..."
python3 cli.py "https://instagram.com/p/..." -o ~/Obsidian/Vault/Inbox
python3 cli.py "https://example.com/article" 

yt2obsidian/
├── cli.py
├── processors/
│   ├── __init__.py
│   ├── base.py
│   ├── youtube.py
│   ├── instagram.py
│   └── webpage.py
├── utils/
│   ├── markdown.py
│   └── helpers.py        # we'll add later
├── output/
└── README.md