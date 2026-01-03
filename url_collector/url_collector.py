#!/usr/bin/env python3
"""
YouTube URL Collector - Enhanced Edition
Searches YouTube and collects video URLs using multiple methods.
Can retrieve 100+ URLs reliably using YouTube's internal API.
"""
import sys
import argparse
import re
import json
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import quote, urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError

APP_NAME = "YouTube URL Collector"
DEFAULT_OUTPUT_DIR = "url_lists"

# Try to import Selenium (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
# METHOD 1: YOUTUBE INTERNAL API (NO SELENIUM, 100+ URLs)
# ═══════════════════════════════════════════════════════════

def extract_api_key(html):
    """Extract YouTube's internal API key from page HTML"""
    patterns = [
        r'"INNERTUBE_API_KEY":"([^"]+)"',
        r'"innertubeApiKey":"([^"]+)"',
        r'ytcfg\.set\(.*?"INNERTUBE_API_KEY":\s*"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def extract_client_data(html):
    """Extract client version and other data from HTML"""
    data = {}
    
    # Client version
    match = re.search(r'"clientVersion":"([^"]+)"', html)
    if match:
        data['clientVersion'] = match.group(1)
    
    # Visitor data
    match = re.search(r'"visitorData":"([^"]+)"', html)
    if match:
        data['visitorData'] = match.group(1)
    
    return data


def get_sort_param(sort_by):
    """Get YouTube sort parameter"""
    sort_params = {
        'date': 'CAISAhAB',        # Upload date
        'views': 'CAMSAhAB',       # View count
        'rating': 'CAESAhAB',      # Rating
        'relevance': None          # Default
    }
    return sort_params.get(sort_by)


def search_youtube_api(query, max_results, sort_by='relevance'):
    """
    Search YouTube using internal API - NO SELENIUM REQUIRED
    Can reliably retrieve 100+ results through continuation tokens.
    """
    print(f"\n🔍 Searching YouTube API...")
    print(f"   Query: {query}")
    print(f"   Target: {max_results} URLs")
    print(f"   Sort: {sort_by}\n")
    
    all_urls = []
    seen_ids = set()
    
    # Step 1: Get initial page to extract API key and context
    encoded_query = quote(query)
    sort_param = get_sort_param(sort_by)
    
    initial_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    if sort_param:
        initial_url += f"&sp={sort_param}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        print("📥 Fetching initial page...")
        req = Request(initial_url, headers=headers)
        with urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        # Extract API key and client data
        api_key = extract_api_key(html)
        if not api_key:
            print("❌ Could not extract API key from page")
            return []
        
        print(f"✅ Found API key: {api_key[:20]}...")
        
        client_data = extract_client_data(html)
        
        # Extract initial data
        match = re.search(r'var ytInitialData = ({.*?});</script>', html, re.DOTALL)
        if not match:
            print("❌ Could not extract initial data")
            return []
        
        initial_data = json.loads(match.group(1))
        
        # Extract videos from initial page
        videos = extract_videos_from_data(initial_data)
        for vid in videos:
            if vid not in seen_ids:
                seen_ids.add(vid)
                all_urls.append(f"https://www.youtube.com/watch?v={vid}")
        
        print(f"   Initial batch: {len(all_urls)} videos")
        
        # Extract continuation token
        continuation = extract_continuation_token(initial_data)
        
        # Step 2: Use continuation tokens to get more results
        api_url = "https://www.youtube.com/youtubei/v1/search"
        
        context = {
            "client": {
                "clientName": "WEB",
                "clientVersion": client_data.get('clientVersion', '2.20231201.00.00'),
            }
        }
        
        if 'visitorData' in client_data:
            context['client']['visitorData'] = client_data['visitorData']
        
        iteration = 1
        max_iterations = 50  # Safety limit
        
        while continuation and len(all_urls) < max_results and iteration < max_iterations:
            print(f"   Fetching batch {iteration + 1}... ({len(all_urls)}/{max_results})", end='\r')
            
            payload = {
                "context": context,
                "continuation": continuation
            }
            
            api_headers = headers.copy()
            api_headers['Content-Type'] = 'application/json'
            
            req = Request(
                f"{api_url}?key={api_key}",
                data=json.dumps(payload).encode('utf-8'),
                headers=api_headers
            )
            
            try:
                with urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                # Extract videos
                videos = extract_videos_from_continuation(data)
                new_count = 0
                for vid in videos:
                    if vid not in seen_ids:
                        seen_ids.add(vid)
                        all_urls.append(f"https://www.youtube.com/watch?v={vid}")
                        new_count += 1
                        if len(all_urls) >= max_results:
                            break
                
                if new_count == 0:
                    print("\n⚠️  No new videos found, stopping...")
                    break
                
                # Get next continuation token
                continuation = extract_continuation_from_ajax(data)
                if not continuation:
                    print("\n✅ Reached end of results")
                    break
                
                iteration += 1
                time.sleep(0.5)  # Be polite to YouTube's servers
                
            except Exception as e:
                print(f"\n⚠️  Error fetching batch {iteration}: {e}")
                break
        
        print(f"\n✅ Collected {len(all_urls)} total URLs")
        return all_urls[:max_results]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def extract_videos_from_data(data):
    """Extract video IDs from ytInitialData"""
    video_ids = []
    
    try:
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        
        for section in contents:
            if 'itemSectionRenderer' in section:
                items = section['itemSectionRenderer']['contents']
                for item in items:
                    if 'videoRenderer' in item:
                        video_id = item['videoRenderer']['videoId']
                        video_ids.append(video_id)
    except (KeyError, TypeError):
        pass
    
    return video_ids


def extract_continuation_token(data):
    """Extract continuation token from initial data"""
    try:
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        
        for section in contents:
            if 'continuationItemRenderer' in section:
                token = section['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
                return token
    except (KeyError, TypeError):
        pass
    
    return None


def extract_videos_from_continuation(data):
    """Extract video IDs from continuation response"""
    video_ids = []
    
    try:
        actions = data['onResponseReceivedCommands']
        for action in actions:
            if 'appendContinuationItemsAction' in action:
                items = action['appendContinuationItemsAction']['continuationItems']
                for item in items:
                    if 'itemSectionRenderer' in item:
                        for content in item['itemSectionRenderer']['contents']:
                            if 'videoRenderer' in content:
                                video_id = content['videoRenderer']['videoId']
                                video_ids.append(video_id)
    except (KeyError, TypeError):
        pass
    
    return video_ids


def extract_continuation_from_ajax(data):
    """Extract next continuation token from API response"""
    try:
        actions = data['onResponseReceivedCommands']
        for action in actions:
            if 'appendContinuationItemsAction' in action:
                items = action['appendContinuationItemsAction']['continuationItems']
                for item in items:
                    if 'continuationItemRenderer' in item:
                        token = item['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
                        return token
    except (KeyError, TypeError):
        pass
    
    return None


# ═══════════════════════════════════════════════════════════
# METHOD 2: SELENIUM (WITH LOGIN SUPPORT)
# ═══════════════════════════════════════════════════════════

def perform_login(driver, wait_time=120):
    """Navigate to YouTube and wait for user to manually log in"""
    try:
        print("\n" + "="*60)
        print("🔐 YouTube Login".center(60))
        print("="*60)
        print("\n📌 Opening YouTube login page...")
        print("⏳ Please log in manually in the browser window")
        print(f"⏱️  You have {wait_time} seconds to complete login")
        print("\n💡 INSTRUCTIONS:")
        print("   1. The browser window will open shortly")
        print("   2. Click 'Sign in' button (top right)")
        print("   3. Enter your Google credentials")
        print("   4. Complete any 2FA if required")
        print("   5. Wait for YouTube homepage to load")
        print("   6. Script will continue automatically")
        print("\n" + "="*60 + "\n")
        
        driver.get("https://www.youtube.com")
        time.sleep(3)
        
        start_time = time.time()
        logged_in = False
        
        print("⏳ Waiting for login... (checking every 5 seconds)")
        
        while time.time() - start_time < wait_time:
            try:
                avatar = driver.find_elements(By.CSS_SELECTOR, "button#avatar-btn, button.ytd-topbar-menu-button-renderer")
                
                if avatar:
                    logged_in = True
                    print("\n✅ Login detected! Continuing with authenticated session...\n")
                    time.sleep(2)
                    break
                
                elapsed = int(time.time() - start_time)
                remaining = wait_time - elapsed
                print(f"   Still waiting... ({remaining}s remaining)", end='\r')
                time.sleep(5)
                
            except Exception:
                pass
        
        if not logged_in:
            print("\n\n⚠️  Login timeout or not detected")
            response = input("\n❓ Continue without login? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ Aborted by user")
                return False
            print("⏭️  Continuing without authentication...\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Login error: {e}")
        return False


def search_youtube_selenium(query, max_results, sort_by="relevance", headless=False, login=False):
    """Search YouTube using Selenium with aggressive scrolling for 100+ URLs"""
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not installed. Use: pip install selenium")
        return []
    
    chrome_options = Options()
    
    if login and headless:
        print("⚠️  Warning: Login requires visible browser. Disabling headless mode.")
        headless = False
    
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    if login:
        profile_dir = Path("./yt_chrome_profile").resolve()
        profile_dir.mkdir(exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument("--profile-directory=Default")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"\n❌ Failed to start Chrome: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Make sure Chrome browser is installed")
        print("   • Try: pip install selenium webdriver-manager")
        print("   • Or use --api method (no Selenium needed)")
        return []

    urls = []
    seen_ids = set()

    try:
        if login:
            if not perform_login(driver):
                return urls
        
        # Build search URL
        encoded_query = quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        sort_param = get_sort_param(sort_by)
        if sort_param:
            search_url += f"&sp={sort_param}"
        
        print(f"🔍 Searching: {query}")
        print(f"📊 Sort by: {sort_by}")
        print(f"🎯 Target: {max_results} videos\n")
        
        driver.get(search_url)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer"))
        )
        
        print("📥 Collecting video URLs with aggressive scrolling...")
        
        scroll_count = 0
        max_scrolls = 200  # Increased limit
        stall_count = 0
        max_stalls = 3
        
        last_count = 0
        
        while len(urls) < max_results and scroll_count < max_scrolls:
            # Extract all video links
            video_elements = driver.find_elements(By.CSS_SELECTOR, "a#video-title, a.yt-simple-endpoint[href*='/watch?v=']")
            
            for elem in video_elements:
                try:
                    href = elem.get_attribute("href")
                    if not href or "/shorts/" in href or "list=" in href:
                        continue
                    
                    match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', href)
                    if match:
                        vid = match.group(1)
                        if vid not in seen_ids:
                            seen_ids.add(vid)
                            urls.append(f"https://www.youtube.com/watch?v={vid}")
                            print(f"   Found: {len(urls)}/{max_results} videos", end='\r')
                            
                            if len(urls) >= max_results:
                                break
                except:
                    continue
            
            if len(urls) >= max_results:
                break
            
            # Check if we're making progress
            if len(urls) == last_count:
                stall_count += 1
                if stall_count >= max_stalls:
                    print(f"\n⚠️  No new videos after {max_stalls} scroll attempts")
                    break
            else:
                stall_count = 0
                last_count = len(urls)
            
            # Aggressive scrolling strategy
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.3)
            
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(1.2)
            
            scroll_count += 1
        
        print(f"\n✅ Collected {len(urls)} video URLs")
        return urls[:max_results]
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return urls
    finally:
        if not login:
            driver.quit()
        else:
            print("\n💡 Browser will close in 5 seconds...")
            time.sleep(5)
            driver.quit()


# ═══════════════════════════════════════════════════════════
# OUTPUT HELPERS
# ═══════════════════════════════════════════════════════════

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
    print('  python url_collector.py "QUERY" -n 100\n')
    
    print("EXAMPLES:")
    print('  Get 100 URLs using API (fast, recommended):')
    print('    python url_collector.py "python tutorials" -n 100\n')
    
    print('  Get 150 URLs sorted by date:')
    print('    python url_collector.py "tech news" -n 150 -s date\n')
    
    print('  Use Selenium with login:')
    print('    python url_collector.py "gaming" -n 100 --selenium --login\n')
    
    print('  Get 500 URLs (API method):')
    print('    python url_collector.py "music" -n 500 -s views\n')
    
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
        description='YouTube URL Collector - Can retrieve 100+ URLs',
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
    print("YouTube URL Collector".center(60))
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