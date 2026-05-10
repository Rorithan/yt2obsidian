#!/usr/bin/env python3
# cli.py

import argparse
import sys
from pathlib import Path

# Auto-detect project root (works anywhere, even with spaces)
PROJECT_ROOT = Path(__file__).parent.resolve()
DEFAULT_OUTPUT = PROJECT_ROOT / "output"

# Import processors
from processors.youtube import YouTubeProcessor
from processors.instagram import InstagramProcessor
from processors.webpage import WebpageProcessor


def main():
    parser = argparse.ArgumentParser(
        description="Convert YouTube, Instagram & webpage links into rich Obsidian markdown."
    )
    parser.add_argument("url", help="URL to process")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--type",
        choices=["auto", "youtube", "instagram", "web"],
        default="auto",
        help="Force processor type"
    )

    args = parser.parse_args()

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        processor = get_processor(args.url, args.type, output_dir)
        md_file = processor.process()
        print(f"✅ Success! Created: {md_file.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def get_processor(url: str, force_type: str, output_dir: Path):
    url_lower = url.lower()

    if force_type == "youtube" or any(x in url_lower for x in ["youtube.com", "youtu.be"]):
        return YouTubeProcessor(url, output_dir)
    elif force_type == "instagram" or "instagram.com" in url_lower:
        return InstagramProcessor(url, output_dir)
    elif force_type == "web":
        return WebpageProcessor(url, output_dir)
    else:
        if any(x in url_lower for x in ["youtube.com", "youtu.be"]):
            return YouTubeProcessor(url, output_dir)
        elif "instagram.com" in url_lower:
            return InstagramProcessor(url, output_dir)
        else:
            return WebpageProcessor(url, output_dir)


if __name__ == "__main__":
    main()