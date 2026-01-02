#!/usr/bin/env python3
"""
Profiles YouTube users based on their comment activity in collected data
"""

import sys
import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

APP_NAME = "YouTube User Profiler"

def load_comments_from_directory(comments_dir):
    """Load all comments from JSON files in directory"""
    comments_dir = Path(comments_dir)
    
    # If relative path, make it relative to script directory
    if not comments_dir.is_absolute():
        script_dir = Path(__file__).parent
        comments_dir = script_dir / comments_dir
    
    if not comments_dir.exists():
        print(f"✗ Error: Directory not found: {comments_dir}")
        return []
    
    json_files = list(comments_dir.glob("*.json"))
    
    if not json_files:
        print(f"✗ Error: No JSON files found in {comments_dir}")
        return []
    
    print(f"Loading comments from {len(json_files)} file(s)...")
    
    all_data = []
    total_comments = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                comments = json.load(f)
                video_id = json_file.stem.split('_')[0] if '_' in json_file.stem else json_file.stem
                
                for comment in comments:
                    comment['_source_file'] = json_file.name
                    comment['_video_id'] = video_id
                    all_data.append(comment)
                
                total_comments += len(comments)
        except Exception as e:
            print(f"✗ Error loading {json_file.name}: {e}")
    
    print(f"✓ Loaded {total_comments} comments from {len(json_files)} videos\n")
    return all_data

def build_user_database(all_comments):
    """Build a database of all users and their comments"""
    user_db = defaultdict(lambda: {
        'comments': [],
        'video_ids': set(),
        'timestamps': [],
        'total_likes': 0,
        'author_id': None,
        'author_url': None,
        'is_verified': False,
        'is_uploader': False
    })
    
    for comment in all_comments:
        author = comment.get('author', 'Unknown')
        
        user_db[author]['comments'].append(comment)
        user_db[author]['video_ids'].add(comment.get('_video_id', 'unknown'))
        user_db[author]['timestamps'].append(comment.get('timestamp', 0))
        user_db[author]['total_likes'] += comment.get('like_count', 0)
        
        if not user_db[author]['author_id']:
            user_db[author]['author_id'] = comment.get('author_id')
            user_db[author]['author_url'] = comment.get('author_url')
            user_db[author]['is_verified'] = comment.get('author_is_verified', False)
            user_db[author]['is_uploader'] = comment.get('author_is_uploader', False)
    
    return user_db

def analyze_user(username, user_data):
    """Perform detailed analysis on a single user"""
    comments = user_data['comments']
    timestamps = [ts for ts in user_data['timestamps'] if ts > 0]
    
    analysis = {
        'username': username,
        'author_id': user_data['author_id'],
        'author_url': user_data['author_url'],
        'is_verified': user_data['is_verified'],
        'is_uploader': user_data['is_uploader'],
        'total_comments': len(comments),
        'videos_participated': len(user_data['video_ids']),
        'total_likes': user_data['total_likes'],
        'avg_likes_per_comment': user_data['total_likes'] / len(comments) if comments else 0,
    }
    
    # Text analysis
    all_text = ' '.join([c.get('text', '') for c in comments])
    words = re.findall(r'\b\w+\b', all_text.lower())
    
    analysis['total_words'] = len(words)
    analysis['avg_comment_length'] = len(all_text) / len(comments) if comments else 0
    analysis['unique_words'] = len(set(words))
    
    # Top keywords (excluding common words)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                   'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been',
                   'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                   'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
                   'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
    
    filtered_words = [w for w in words if w not in common_words and len(w) > 2]
    word_freq = Counter(filtered_words)
    analysis['top_keywords'] = word_freq.most_common(10)
    
    # Temporal analysis
    if timestamps:
        timestamps.sort()
        analysis['first_comment'] = datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
        analysis['last_comment'] = datetime.fromtimestamp(timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S')
        
        time_span_days = (timestamps[-1] - timestamps[0]) / 86400
        analysis['activity_span_days'] = round(time_span_days, 1)
        
        if time_span_days > 0:
            analysis['comments_per_day'] = round(len(comments) / time_span_days, 2)
        else:
            analysis['comments_per_day'] = len(comments)
        
        # Activity hours
        hours = [datetime.fromtimestamp(ts).hour for ts in timestamps]
        hour_freq = Counter(hours)
        most_active_hour = hour_freq.most_common(1)[0] if hour_freq else (0, 0)
        analysis['most_active_hour'] = f"{most_active_hour[0]:02d}:00-{most_active_hour[0]+1:02d}:00"
    else:
        analysis['first_comment'] = 'Unknown'
        analysis['last_comment'] = 'Unknown'
        analysis['activity_span_days'] = 0
        analysis['comments_per_day'] = 0
        analysis['most_active_hour'] = 'Unknown'
    
    # Engagement analysis
    reply_count = sum(1 for c in comments if c.get('parent') != 'root')
    analysis['reply_comments'] = reply_count
    analysis['root_comments'] = len(comments) - reply_count
    analysis['reply_ratio'] = round(reply_count / len(comments) * 100, 1) if comments else 0
    
    return analysis

def display_user_profile(analysis):
    """Display detailed user profile"""
    print("\n" + "="*70)
    print(f"USER PROFILE: {analysis['username']}")
    print("="*70)
    
    print("\nBASIC INFORMATION:")
    print(f"  Author ID: {analysis['author_id'] or 'N/A'}")
    print(f"  Profile URL: {analysis['author_url'] or 'N/A'}")
    print(f"  Verified: {'Yes' if analysis['is_verified'] else 'No'}")
    print(f"  Channel Owner: {'Yes' if analysis['is_uploader'] else 'No'}")
    
    print("\nACTIVITY METRICS:")
    print(f"  Total Comments: {analysis['total_comments']}")
    print(f"  Videos Participated: {analysis['videos_participated']}")
    print(f"  First Comment: {analysis['first_comment']}")
    print(f"  Last Comment: {analysis['last_comment']}")
    print(f"  Activity Span: {analysis['activity_span_days']} days")
    print(f"  Comments per Day: {analysis['comments_per_day']}")
    print(f"  Most Active Hour: {analysis['most_active_hour']}")
    
    print("\nENGAGEMENT:")
    print(f"  Total Likes Received: {analysis['total_likes']}")
    print(f"  Average Likes per Comment: {analysis['avg_likes_per_comment']:.2f}")
    print(f"  Root Comments: {analysis['root_comments']}")
    print(f"  Reply Comments: {analysis['reply_comments']} ({analysis['reply_ratio']}%)")
    
    print("\nCONTENT ANALYSIS:")
    print(f"  Total Words: {analysis['total_words']}")
    print(f"  Unique Words: {analysis['unique_words']}")
    print(f"  Avg Comment Length: {analysis['avg_comment_length']:.1f} characters")
    
    print("\nTOP KEYWORDS:")
    for i, (word, count) in enumerate(analysis['top_keywords'], 1):
        print(f"  {i}. '{word}' - {count} times")
    
    print("\n" + "="*70 + "\n")

def display_top_users(user_db, limit=20, sort_by='comments'):
    """Display top users by activity"""
    print(f"\n{'='*70}")
    print(f"TOP {limit} USERS BY {sort_by.upper()}")
    print(f"{'='*70}\n")
    
    # Sort users
    if sort_by == 'comments':
        sorted_users = sorted(user_db.items(), 
                            key=lambda x: len(x[1]['comments']), 
                            reverse=True)
    elif sort_by == 'videos':
        sorted_users = sorted(user_db.items(), 
                            key=lambda x: len(x[1]['video_ids']), 
                            reverse=True)
    elif sort_by == 'likes':
        sorted_users = sorted(user_db.items(), 
                            key=lambda x: x[1]['total_likes'], 
                            reverse=True)
    else:
        sorted_users = sorted(user_db.items(), 
                            key=lambda x: len(x[1]['comments']), 
                            reverse=True)
    
    sorted_users = sorted_users[:limit]
    
    print(f"{'#':<4} {'Username':<30} {'Comments':<10} {'Videos':<8} {'Likes':<8}")
    print("-" * 70)
    
    for i, (username, data) in enumerate(sorted_users, 1):
        username_display = username[:28] + '..' if len(username) > 30 else username
        comments_count = len(data['comments'])
        videos_count = len(data['video_ids'])
        likes_count = data['total_likes']
        
        print(f"{i:<4} {username_display:<30} {comments_count:<10} {videos_count:<8} {likes_count:<8}")
    
    print("\n" + "="*70 + "\n")

def find_cross_video_users(user_db, min_videos=2):
    """Find users who commented on multiple videos"""
    cross_video_users = {
        username: data 
        for username, data in user_db.items() 
        if len(data['video_ids']) >= min_videos
    }
    
    return cross_video_users

def export_profile(analysis, output_file):
    """Export user profile to JSON"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"✓ Profile exported to: {output_file}")
    except Exception as e:
        print(f"✗ Error exporting profile: {e}")

def main():
    # Check if no arguments provided
    if len(sys.argv) == 1:
        print("\n" + "="*60)
        print(APP_NAME.center(60))
        print("="*60)
        print("\n✗ Error: No arguments provided\n")
        print("Usage: python user_profiler.py [OPTIONS]\n")
        print("This tool analyzes YouTube users from your DOWNLOADED comment files which are onbtained via comment_collector.py.")
        print("It searches through JSON files in comment_sections/ (or custom -d directory)\n")
        print("Examples:")
        print('  python user_profiler.py -u "@Username"')
        print('  python user_profiler.py -u "@Username" -d comment_sections')
        print('  python user_profiler.py --top 20')
        print('  python user_profiler.py --cross-video 3')
        print('  python user_profiler.py -u "@User" -d case_comments -o profile.json')
        print("\nFor more help, use: python user_profiler.py -h\n")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='Profile YouTube users based on their comment activity in downloaded JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
HOW IT WORKS:
This tool analyzes users from your DOWNLOADED YouTube comment files which are obtained via comment_collector.py
It reads JSON files created by comment_collector.py and builds user profiles.

REQUIRED:
You must have comment JSON files in a directory (default: comment_sections/)
These files are created by running comment_collector.py first.

Examples:
  # Profile a specific user (searches in comment_sections/ by default)
  %(prog)s -u "@SuspiciousUser"
  
  # Profile user from custom directory
  %(prog)s -u "@Username" -d ./case_comments
  
  # Show top 20 most active users from downloaded comments
  %(prog)s --top 20
  
  # Find users who commented on 3+ videos in your dataset
  %(prog)s --cross-video 3
  
  # Profile user and export to JSON
  %(prog)s -u "@Username" -o user_profile.json
  
  # Show top users sorted by likes (from custom directory)
  %(prog)s --top 15 --sort-by likes -d cold_case_comments

WORKFLOW:
1. First run: python comment_collector.py -f urls.txt
2. Then run: python user_profiler.py -u "@Username"

Note: This tool only analyzes data from your downloaded comment files.
It cannot access user activity outside your collected dataset.
        """
    )
    
    parser.add_argument(
        '-u', '--user',
        help='Username to profile (e.g., "@Username")'
    )
    
    parser.add_argument(
        '-d', '--dir',
        default='comment_sections',
        help='Directory containing comment JSON files (default: comment_sections)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        metavar='N',
        help='Show top N most active users'
    )
    
    parser.add_argument(
        '--sort-by',
        choices=['comments', 'videos', 'likes'],
        default='comments',
        help='Sort top users by: comments, videos, or likes (default: comments)'
    )
    
    parser.add_argument(
        '--cross-video',
        type=int,
        metavar='N',
        help='Find users who commented on N or more videos'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Export profile to JSON file'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "="*70)
    print(APP_NAME.center(70))
    print("="*70 + "\n")
    
    # Load all comments
    all_comments = load_comments_from_directory(args.dir)
    
    if not all_comments:
        sys.exit(1)
    
    # Build user database
    print("Building user database...")
    user_db = build_user_database(all_comments)
    print(f"✓ Found {len(user_db)} unique users\n")
    
    # Handle different modes
    if args.user:
        # Profile specific user
        if args.user not in user_db:
            print(f"✗ User '{args.user}' not found in collected comments")
            print(f"\nDid you mean one of these similar usernames?")
            
            similar = [u for u in user_db.keys() if args.user.lower() in u.lower()][:5]
            for s in similar:
                print(f"  - {s}")
            sys.exit(1)
        
        analysis = analyze_user(args.user, user_db[args.user])
        display_user_profile(analysis)
        
        if args.output:
            export_profile(analysis, args.output)
    
    elif args.top:
        # Show top users
        display_top_users(user_db, limit=args.top, sort_by=args.sort_by)
    
    elif args.cross_video:
        # Find cross-video users
        cross_users = find_cross_video_users(user_db, min_videos=args.cross_video)
        
        print(f"Found {len(cross_users)} users who commented on {args.cross_video}+ videos:\n")
        
        sorted_cross = sorted(cross_users.items(), 
                            key=lambda x: len(x[1]['video_ids']), 
                            reverse=True)
        
        for username, data in sorted_cross[:50]:
            print(f"  {username}")
            print(f"    Videos: {len(data['video_ids'])} | Comments: {len(data['comments'])} | Likes: {data['total_likes']}")
        
        print()
    
    else:
        # No specific action, show summary
        print("No specific action requested. Use -h for help.\n")
        print("Quick summary:")
        print(f"  Total users: {len(user_db)}")
        print(f"  Total comments: {len(all_comments)}")
        print(f"\nTry: python user_profiler.py --top 10")

if __name__ == "__main__":
    main()