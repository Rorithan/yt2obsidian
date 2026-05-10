#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import argparse
from core import get_processor
from config import Config

def interactive_mode():
    print("🎥 yt-md - YouTube & Instagram → Obsidian Markdown")
    print("Paste link and press Enter (Ctrl+C to quit)\n")
    
    while True:
        try:
            url = input("Paste link here: ").strip()
            if not url:
                continue
                
            Config.ensure_dirs()
            processor = get_processor(url)
            processor.process()
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")

def cli_mode():
    parser = argparse.ArgumentParser(description="yt-md - Rich Markdown for Obsidian")
    parser.add_argument("url", nargs="?", help="URL to process")
    parser.add_argument("-o", "--output", type=Path, help="Base output directory")
    # Add more flags later if needed

    args = parser.parse_args()
    if args.output:
        Config.set_paths(md=args.output, images=args.output, videos=args.output)

    if args.url:
        processor = get_processor(args.url)
        processor.process()
    else:
        interactive_mode()

if __name__ == "__main__":
    cli_mode()