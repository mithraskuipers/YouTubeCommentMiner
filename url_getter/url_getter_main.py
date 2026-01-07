#!/usr/bin/env python3
"""
YouTube URL Getter - Enhanced Edition
Main entry point and CLI interface.
"""
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime

from url_getter_api import search_youtube_api
from url_getter_selenium import search_youtube_selenium, SELENIUM_AVAILABLE

APP_NAME = "YouTube URL Getter"
DEFAULT_OUTPUT_DIR = "url_lists"


def save_urls(urls, output_file):
    """Save URLs to a text file"""
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
        print(f"\n✅ URLs saved to: {output_file}")
        return True
    except Exception as e:
        print(f"\n❌ Error saving URLs: {e}")
        return False


def preview_urls(urls, preview_count=5):
    """Display a preview of the URLs"""
    print(f"\n📋 Preview (first {min(preview_count, len(urls))} URLs):")
    print("-" * 60)
    for i, url in enumerate(urls[:preview_count], 1):
        print(f"{i}. {url}")
    if len(urls) > preview_count:
        print(f"... and {len(urls) - preview_count} more")
    print("-" * 60)


def generate_output_filename(query, sort_by, max_results, output_dir=DEFAULT_OUTPUT_DIR):
    """Generate a descriptive filename"""
    safe_query = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)
    safe_query = re.sub(r'_+', '_', safe_query)
    safe_query = safe_query.strip('_').lower()
    safe_query = safe_query[:60]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"yt_urls_{safe_query}_{sort_by}_n{max_results}_{timestamp}.txt"
    return str(Path(output_dir) / filename)


def print_help():
    """Print usage help"""
    print("\n" + "="*70)
    print(APP_NAME.center(70))
    print("="*70)
    print("\n🚀 ENHANCED VERSION - Can retrieve 100+ URLs!\n")
    
    print("METHODS:")
    print("  --api      : YouTube Internal API (DEFAULT, NO SELENIUM)")
    print("               ✅ Fast, reliable, 100+ URLs easily")
    print("               ✅ No browser needed")
    print("  --selenium : Browser automation with Selenium")
    print("               ⚠️  Requires Chrome + Selenium")
    print("               ✅ Can use --login for authentication\n")
    
    print("BASIC USAGE:")
    print('  python url_getter_main.py "QUERY" -n 100\n')
    
    print("EXAMPLES:")
    print('  Get 100 URLs using API (fast, recommended):')
    print('    python url_getter_main.py "python tutorials" -n 100\n')
    
    print('  Get 150 URLs sorted by date:')
    print('    python url_getter_main.py "tech news" -n 150 -s date\n')
    
    print('  Use Selenium with login:')
    print('    python url_getter_main.py "gaming" -n 100 --selenium --login\n')
    
    print('  Get 500 URLs (API method):')
    print('    python url_getter_main.py "music" -n 500 -s views\n')
    
    print("OPTIONS:")
    print("  -n, --max NUM       Number of URLs to collect (default: 10)")
    print("  -s, --sort TYPE     Sort: relevance, date, views, rating")
    print("  -o, --output FILE   Output filename")
    print("  --api               Use YouTube API (default, fast)")
    print("  --selenium          Use Selenium browser automation")
    print("  --login             Login before searching (Selenium only)")
    print("  --no-preview        Skip URL preview")
    print("\n" + "="*70 + "\n")


def main():
    if len(sys.argv) == 1 or '--help' in sys.argv or 'help' in sys.argv:
        print_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description='YouTube URL Getter - Can retrieve 100+ URLs',
        add_help=False
    )

    parser.add_argument('query', help='Search query')
    parser.add_argument('-n', '--max', type=int, default=10, help='Max results (default: 10)')
    parser.add_argument('-s', '--sort', choices=['relevance', 'date', 'views', 'rating'],
                        default='relevance', help='Sort order')
    parser.add_argument('-o', '--output', default=None, help='Output filename')
    parser.add_argument('--api', action='store_true', help='Use YouTube API (default)')
    parser.add_argument('--selenium', action='store_true', help='Use Selenium browser')
    parser.add_argument('--login', action='store_true', help='Login with Selenium')
    parser.add_argument('--no-preview', action='store_true', help='Skip preview')
    parser.add_argument('--help', action='store_true', help='Show help')

    args = parser.parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    if args.max <= 0:
        print("\n❌ Error: Maximum results must be greater than 0")
        sys.exit(1)

    print("\n" + "="*60)
    print("YouTube URL Getter".center(60))
    print("="*60)

    # Determine method
    use_selenium = args.selenium or args.login
    
    if use_selenium:
        print("\n🌐 Method: Selenium Browser Automation")
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not installed!")
            print("   Install: pip install selenium")
            print("   Or use API method (remove --selenium flag)")
            sys.exit(1)
        
        urls = search_youtube_selenium(
            args.query,
            args.max,
            args.sort,
            headless=False,
            login=args.login
        )
    else:
        print("\n🚀 Method: YouTube Internal API (Fast)")
        urls = search_youtube_api(args.query, args.max, args.sort)

    if not urls:
        print("\n❌ No URLs found")
        sys.exit(1)

    if not args.no_preview:
        preview_urls(urls)

    # Generate output filename
    if args.output:
        output_path = Path(args.output)
        if output_path.parent == Path('.'):
            output_file = str(Path(DEFAULT_OUTPUT_DIR) / args.output)
        else:
            output_file = args.output
    else:
        output_file = generate_output_filename(args.query, args.sort, args.max)

    if save_urls(urls, output_file):
        print(f"\n{'='*60}")
        print(f"✅ Success! Collected {len(urls)} video URLs")
        print(f"📁 File: {output_file}")
        print(f"🔍 Query: '{args.query}'")
        print(f"📊 Sort: {args.sort}")
        print(f"🎯 Requested: {args.max}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()