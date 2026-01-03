#!/usr/bin/env python3
"""
YouTube Comment Collector
Downloads YouTube comments and exports them as comments-only JSON files.
"""

import subprocess
import sys
import platform
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from pathlib import Path
import platform

APP_NAME = "YouTube Comment Collector"


# ───────────────────────────────
# Banner
# ───────────────────────────────

def print_intro_banner():
    print("\n" + "=" * 70)
    print(APP_NAME.center(70))
    print("=" * 70)
    print("Collect full YouTube comment sections using yt-dlp".center(70))
    print("=" * 70 + "\n")


# ───────────────────────────────
# yt-dlp Helpers
# ───────────────────────────────

def get_default_ytdlp_path():
    script_dir = Path(__file__).parent.resolve()
    bin_dir = script_dir.parent / "bin"  # Goes up one level to the project root, then into bin
    exe_name = "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp"
    return bin_dir / exe_name


def find_ytdlp_executable(custom_path=None):
    if custom_path:
        p = Path(custom_path)
        return str(p) if p.exists() else None

    # 1. ./bin/yt-dlp
    default = get_default_ytdlp_path()
    if default.exists():
        return str(default)

    # 2. PATH
    try:
        subprocess.run(
            ["yt-dlp", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "yt-dlp"
    except Exception:
        return None



# ───────────────────────────────
# Utilities
# ───────────────────────────────

def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return url.rstrip("/").split("/")[-1]


def read_urls_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


# ───────────────────────────────
# Core Logic
# ───────────────────────────────

def download_comments(url, output_dir, ytdlp_path):
    video_id = extract_video_id(url)

    output_template = output_dir / f"{video_id}.%(ext)s"
    comments_json = output_dir / f"{video_id}.comments.json"
    info_json = output_dir / f"{video_id}.info.json"

    cmd = [
        ytdlp_path,
        "--skip-download",
        "--write-comments",
        "--write-info-json",
        "--no-write-thumbnail",
        "--no-write-description",
        "--no-write-subs",
        "--no-write-auto-subs",
        "--no-playlist",
        "--extractor-args",
        "youtube:comment_sort=top;max_comments=all",
        "-o",
        str(output_template),
        url,
    ]

    print(f"\nProcessing: {url}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("✗ yt-dlp failed")
        return False

    if not comments_json.exists():
        print("✗ comments.json not created")
        return False

    # Optional cleanup
    if info_json.exists():
        info_json.unlink()

    print(f"✓ Saved comments: {comments_json.name}")
    return True


# ───────────────────────────────
# Main
# ───────────────────────────────

def main():
    print_intro_banner()

    parser = argparse.ArgumentParser(
        description="Download YouTube comment sections using yt-dlp"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--urls", nargs="+")
    group.add_argument("-f", "--file")

    parser.add_argument("-o", "--output-dir", default="comment_sections")
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--ytdlp-path")

    args = parser.parse_args()

    ytdlp_path = find_ytdlp_executable(args.ytdlp_path)
    if not ytdlp_path:
        print("✗ yt-dlp not found")
        sys.exit(1)

    if args.file:
        urls = read_urls_from_file(args.file)
        output_dir = Path(args.output_dir) / Path(args.file).stem
    else:
        urls = args.urls
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}]")
        if download_comments(url, output_dir, ytdlp_path):
            success += 1
        if args.delay and i < len(urls):
            time.sleep(args.delay)

    print("\n" + "=" * 70)
    print(f"Completed: {success}/{len(urls)}")
    print(f"Output: {output_dir.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
