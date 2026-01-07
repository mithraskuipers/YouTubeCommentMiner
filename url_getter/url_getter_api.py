"""
YouTube API Search Module
Uses YouTube's internal API to collect video URLs without Selenium.
Can reliably retrieve 100+ URLs using continuation tokens.
"""
import re
import json
import time
from urllib.parse import quote
from urllib.request import urlopen, Request


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