#!/usr/bin/env python3
"""
YouTube URL Collector
Searches YouTube and collects video URLs.
Auto-generated filenames include all settings for easy tracking.
"""
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus
from urllib.request import urlopen, Request
from urllib.error import URLError

APP_NAME = "YouTube URL Collector"
DEFAULT_OUTPUT_DIR = "url_lists"


def get_sort_param(sort_by):
    """Get the YouTube sort parameter based on user choice"""
    sort_params = {
        'date': 'CAI%3D',      # Upload date (newest first)
        'views': 'CAMSAhAB',   # View count (most viewed)
        'rating': 'CAESAhAB',  # Rating (highest rated)
        'relevance': ''        # Default/relevance (no parameter)
    }
    return sort_params.get(sort_by, '')


def build_search_url(query, sort_by='relevance'):
    """Build YouTube search URL with optional sorting parameters"""
    encoded_query = quote_plus(query)
    base_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    sort_param = get_sort_param(sort_by)
    if sort_param:
        base_url += f"&sp={sort_param}"

    return base_url


def extract_video_ids(html_content):
    """Extract video IDs from YouTube search results HTML"""
    pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
    video_ids = re.findall(pattern, html_content)

    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for vid_id in video_ids:
        if vid_id not in seen:
            seen.add(vid_id)
            unique_ids.append(vid_id)

    return unique_ids


def search_youtube(query, max_results, sort_by):
    """Search YouTube and return list of video URLs"""
    print(f"\n{'='*60}")
    print(f"Searching YouTube for: '{query}'")
    print(f"Max results requested: {max_results}")
    print(f"Sort by: {sort_by}")
    print(f"{'='*60}\n")

    search_url = build_search_url(query, sort_by)
    print(f"Search URL: {search_url}\n")
    print("Fetching results... This may take a moment.\n")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = Request(search_url, headers=headers)

        with urlopen(req, timeout=30) as response:
            html_content = response.read().decode('utf-8')

        video_ids = extract_video_ids(html_content)
        video_ids = video_ids[:max_results]

        urls = [f"https://www.youtube.com/watch?v={vid_id}" for vid_id in video_ids]

        print(f"✓ Found {len(urls)} video(s)")
        return urls

    except URLError as e:
        print(f"✗ Error fetching YouTube search results")
        print(f" Error message: {e.reason}")
        return []
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return []


def save_urls(urls, output_file):
    """Save URLs to a text file"""
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
        print(f"\n✓ URLs saved to: {output_file}")
        return True
    except Exception as e:
        print(f"\n✗ Error saving URLs: {e}")
        return False


def preview_urls(urls, preview_count=5):
    """Display a preview of the URLs"""
    print(f"\nPreview (first {min(preview_count, len(urls))} URLs):")
    print("-" * 60)
    for i, url in enumerate(urls[:preview_count], 1):
        print(f"{i}. {url}")
    if len(urls) > preview_count:
        print(f"... and {len(urls) - preview_count} more")
    print("-" * 60)


def generate_output_filename(query, sort_by, max_results, output_dir=DEFAULT_OUTPUT_DIR):
    """Generate a descriptive filename including all key settings"""
    safe_query = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)
    safe_query = re.sub(r'_+', '_', safe_query)
    safe_query = safe_query.strip('_').lower()
    safe_query = safe_query[:60]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_part = f"n{max_results}"

    filename = f"yt_urls_{safe_query}_{sort_by}_{results_part}_{timestamp}.txt"
    return str(Path(output_dir) / filename)


def print_detailed_help():
    """Print detailed usage examples and help"""
    print("\n" + "="*70)
    print(APP_NAME.center(70))
    print("="*70)
    print("\n📖 USAGE GUIDE\n")

    print("BASIC SYNTAX:")
    print(" python url_collector.py \"SEARCH QUERY\" [OPTIONS]\n")

    print("="*70)
    print("\n🔍 SEARCH QUERY EXAMPLES:\n")

    print("Simple search:")
    print(' python url_collector.py "python tutorials"')
    print(' python url_collector.py "cooking recipes"\n')

    print("Combined search terms (multiple words):")
    print(' python url_collector.py "machine learning basics"')
    print(' python url_collector.py "how to fix car engine"')
    print(' python url_collector.py "best gaming laptops 2024"\n')

    print("Search with operators (use quotes!):")
    print(' python url_collector.py "python AND pandas"')
    print(' python url_collector.py "travel vlog thailand"')
    print(' python url_collector.py "guitar tutorial beginner"\n')

    print("="*70)
    print("\n📊 SORTING OPTIONS:\n")

    print("Sort by RELEVANCE (default):")
    print(' python url_collector.py "javascript" -s relevance')
    print(' python url_collector.py "javascript" # same as above\n')

    print("Sort by DATE (newest first):")
    print(' python url_collector.py "tech news" -s date')
    print(' python url_collector.py "gaming highlights" --sort date\n')

    print("Sort by VIEWS (most viewed first):")
    print(' python url_collector.py "music videos" -s views')
    print(' python url_collector.py "viral videos" --sort views\n')

    print("Sort by RATING (highest rated first):")
    print(' python url_collector.py "documentary" -s rating')
    print(' python url_collector.py "educational content" --sort rating\n')

    print("="*70)
    print("\n🔢 LIMITING RESULTS:\n")

    print("Get first 10 videos (default):")
    print(' python url_collector.py "cooking"\n')

    print("Get first 50 videos:")
    print(' python url_collector.py "python tutorials" -n 50')
    print(' python url_collector.py "python tutorials" --max 50\n')

    print("Get first 100 videos:")
    print(' python url_collector.py "fitness workouts" -n 100\n')

    print("Get first 5 videos only:")
    print(' python url_collector.py "quick recipes" -n 5\n')

    print("⚠️ NOTE: YouTube returns ~20-30 results per page.")
    print(" Requesting 100+ results may only return 20-30 actual URLs.\n")

    print("="*70)
    print("\n💾 OUTPUT FILE OPTIONS:\n")

    print("Auto-generated filename (default - saved in ./url_lists/):")
    print(' python url_collector.py "travel vlogs" -n 50')
    print(" → Creates: ./url_lists/yt_urls_travel_vlogs_relevance_n50_20260102_143022.txt\n")

    print("Custom filename (still in ./url_lists/):")
    print(' python url_collector.py "music" -n 30 -o my_music.txt')
    print(" → Creates: ./url_lists/my_music.txt\n")

    print("Custom filename with custom directory:")
    print(' python url_collector.py "coding" -o my_dir/code_videos.txt')
    print(" → Creates: ./my_dir/code_videos.txt\n")

    print("="*70)
    print("\n🎯 COMPLETE EXAMPLES:\n")

    print("Example 1: Get 50 newest Python tutorials")
    print(' python url_collector.py "python programming tutorial" -n 50 -s date\n')

    print("Example 2: Get 100 most viewed music videos")
    print(' python url_collector.py "music video" -n 100 -s views -o top_music.txt\n')

    print("Example 3: Get 25 highest rated documentaries")
    print(' python url_collector.py "documentary" -n 25 -s rating\n')

    print("Example 4: Get 10 most relevant cooking videos (no preview)")
    print(' python url_collector.py "cooking recipes" -n 10 --no-preview\n')

    print("Example 5: Complex search with combined terms")
    print(' python url_collector.py "artificial intelligence machine learning" -n 50 -s date\n')

    print("Example 6: Get recent gaming content")
    print(' python url_collector.py "gaming highlights 2024" -n 30 -s date -o gaming.txt\n')

    print("="*70)
    print("\n❌ COMMON MISTAKES TO AVOID:\n")

    print("❌ Missing quotes around multi-word searches:")
    print(" python url_collector.py python tutorials # WRONG")
    print(' python url_collector.py "python tutorials" # CORRECT\n')

    print("❌ Invalid sort option:")
    print(" python url_collector.py \"music\" -s popular # WRONG")
    print(" python url_collector.py \"music\" -s views # CORRECT\n")

    print("❌ Typo in sort option:")
    print(" python url_collector.py \"videos\" -s view # WRONG (singular)")
    print(" python url_collector.py \"videos\" -s views # CORRECT (plural)\n")

    print("❌ Unrealistic expectations:")
    print(" python url_collector.py \"test\" -n 1000")
    print(" → Will likely only return ~20-30 URLs due to YouTube limitations\n")

    print("="*70)
    print("\n💡 TIPS:\n")

    print("• Use quotes around searches with spaces")
    print("• Be specific in your search terms for better results")
    print("• Combine sorting and limits for targeted results")
    print("• Check the preview before processing large batches")
    print("• Sort by 'date' for recent content, 'views' for popular content")
    print("• YouTube limits results per page to ~20-30 videos")
    print(f"• Files are saved in ./{DEFAULT_OUTPUT_DIR}/ by default")
    print("• For comprehensive scraping, consider using yt-dlp integration\n")

    print("="*70)
    print("\nFor command-line help: python url_collector.py -h")
    print("="*70 + "\n")


def main():
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['help', '--help-detailed', '-hh']):
        if len(sys.argv) == 2 and sys.argv[1] in ['help', '--help-detailed', '-hh']:
            print_detailed_help()
        else:
            print("\n" + "="*70)
            print(APP_NAME.center(70))
            print("="*70)
            print("\n❌ Error: No search query provided\n")
            print("BASIC USAGE:")
            print(' python url_collector.py "SEARCH QUERY" [OPTIONS]\n')
            print("QUICK EXAMPLES:\n")
            print(" Get 50 Python tutorials sorted by date:")
            print(' python url_collector.py "python tutorials" -n 50 -s date\n')
            print(" Get 100 most viewed music videos:")
            print(' python url_collector.py "music video" -n 100 -s views\n')
            print(" Get 25 highest rated documentaries:")
            print(' python url_collector.py "documentary" -n 25 -s rating\n')
            print(" Search with combined terms:")
            print(' python url_collector.py "machine learning tutorial" -n 50\n')
            print("SORTING OPTIONS: relevance, date, views, rating")
            print("LIMIT RESULTS: Use -n or --max (e.g., -n 50 for first 50 videos)\n")
            print(f"OUTPUT: Files saved to ./{DEFAULT_OUTPUT_DIR}/ by default\n")
            print("📖 For detailed help with examples: python url_collector.py help")
            print("⚙️ For command options: python url_collector.py -h\n")
            print("="*70 + "\n")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Search YouTube and collect video URLs (no external dependencies required)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
QUICK EXAMPLES:
  Get 50 Python tutorials (sorted by relevance):
    %(prog)s "python tutorials" -n 50

  Get 100 most viewed music videos:
    %(prog)s "music video" -n 100 -s views

  Get 25 newest documentaries:
    %(prog)s "documentary" -n 25 -s date -o docs.txt

  Search with combined terms:
    %(prog)s "machine learning tutorial" -n 50 -s rating

SORT OPTIONS:
  relevance - Default YouTube relevance ranking
  date      - Upload date (newest first)
  views     - View count (highest first)
  rating    - Rating (highest rated first)

COMBINING SEARCH TERMS:
  Simply include multiple words in quotes:
    "python programming tutorial"
    "best gaming laptops 2024"
    "how to cook pasta"

OUTPUT:
  Files are saved to ./url_lists/ by default
  Use -o to specify a custom filename or path

NOTE: YouTube typically returns 20-30 results per page.
For detailed help: python url_collector.py help
        """
    )

    parser.add_argument('query', help='Search query string (use quotes for multi-word searches: "python tutorials")')
    parser.add_argument('-n', '--max', type=int, default=10,
                        help='Maximum number of results (default: 10). Example: -n 50 for first 50 videos')
    parser.add_argument('-s', '--sort', choices=['relevance', 'date', 'views', 'rating'],
                        default='relevance', help='Sort order: relevance (default), date (newest), views (most viewed), rating (highest rated)')
    parser.add_argument('-o', '--output', default=None,
                        help=f'Output filename. Default: auto-generated in ./{DEFAULT_OUTPUT_DIR}/')
    parser.add_argument('--no-preview', action='store_true', help='Skip URL preview display')

    args = parser.parse_args()

    if args.max <= 0:
        print("\n❌ Error: Maximum results must be greater than 0")
        print(f" You specified: -n {args.max}")
        print(" Try: -n 10 (or any positive number)\n")
        sys.exit(1)

    if args.max > 100:
        print(f"\n⚠️ Warning: You requested {args.max} results.")
        print(" YouTube typically returns only 20-30 results per page.")
        print(" You may receive fewer results than requested.\n")

    print("\n" + "="*60)
    print("YouTube URL Collector".center(60))
    print("="*60)

    urls = search_youtube(args.query, args.max, args.sort)

    if not urls:
        print("\n❌ No URLs found or an error occurred")
        print("\nTROUBLESHOOTING:")
        print(" • Check your internet connection")
        print(" • Verify your search query is valid")
        print(" • Try a different search term")
        print(" • YouTube may be blocking automated requests\n")
        sys.exit(1)

    if not args.no_preview:
        preview_urls(urls)

    if args.output:
        # If user provides custom output, check if it includes a directory
        output_path = Path(args.output)
        if output_path.parent == Path('.'):
            # No directory specified, add default directory
            output_file = str(Path(DEFAULT_OUTPUT_DIR) / args.output)
        else:
            # User specified a directory, use as-is
            output_file = args.output
    else:
        # Auto-generate filename in default directory
        output_file = generate_output_filename(args.query, args.sort, args.max)

    if save_urls(urls, output_file):
        print(f"\n{'='*60}")
        print(f"✅ Success! Collected {len(urls)} video URLs")
        print(f"📁 Output file: {output_file}")
        print(f"🔍 Search query: '{args.query}'")
        print(f"📊 Sorted by: {args.sort}")
        print(f"🔢 Requested: {args.max} results")
        print(f"{'='*60}\n")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()