# yt2obsidian

terminal command for any supported link:
python3 cli.py ""

A lightweight macOS terminal tool that turns YouTube, Instagram, and webpage links into rich Obsidian-ready Markdown files.

## Quick Start (Terminal)

cd ~/yt2obsidian
python3 -m venv venv && source venv/bin/activate

## Features
- Auto-detects content type or force with `--type`
- YouTube: title, description, uploader, date, thumbnail embed, subtitles (if available)
- Instagram: post/reel metadata + caption
- Webpages: clean title, main content, metadata
- Safe filenames, YAML frontmatter for Obsidian
- Zero bloat — uses built-ins + minimal dependencies

## Installation and dependancies

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
├── utils.py
├── output/
└── README.md