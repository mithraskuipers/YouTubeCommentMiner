"""
YouTube Selenium Search Module
Browser automation with login support for authenticated searches.
"""
import re
import time
from pathlib import Path
from urllib.parse import quote

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


def get_sort_param(sort_by):
    """Get YouTube sort parameter"""
    sort_params = {
        'date': 'CAISAhAB',        # Upload date
        'views': 'CAMSAhAB',       # View count
        'rating': 'CAESAhAB',      # Rating
        'relevance': None          # Default
    }
    return sort_params.get(sort_by)


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