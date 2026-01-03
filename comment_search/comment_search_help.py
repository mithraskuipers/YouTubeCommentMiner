"""
Help text and argument parser configuration for YouTube Comment Search
"""

import argparse

def get_usage_examples():
    """Return quick usage examples for no-args display"""
    return """Examples:
  # Search for keywords
  python comment_search.py -d ./comments "deep web" "murder"

  # Find most active users
  python comment_search.py -d ./comments --most-active 20

  # Extract all comments from a user
  python comment_search.py -d ./comments --user "John Doe"

  # Search within a specific user's comments
  python comment_search.py -d ./comments --user "John Doe" "keyword"
"""

def get_arg_parser():
    """Create and return configured argument parser"""
    parser = argparse.ArgumentParser(
        description='Search through YouTube comment JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for any keyword (saves JSON by default)
  %(prog)s -d ./comments "deep web" "murder" "photo"
  
  # Search requiring ALL keywords
  %(prog)s -d ./comments "deep web" "murder" -m all
  
  # Find the 20 most active users
  %(prog)s -d ./comments --most-active 20
  
  # Export most active users to DOCX
  %(prog)s -d ./comments --most-active 20 --export docx json
  
  # Extract all comments from a specific user
  %(prog)s -d ./comments --user "John Doe"
  
  # Search within a specific user's comments
  %(prog)s -d ./comments --user "John Doe" "murder" "deep web"
  
  # Search user's comments with filters
  %(prog)s -d ./comments --user "John Doe" "keyword" --min-likes 5 -m all
  
  # Export user's comments to DOCX
  %(prog)s -d ./comments --user "John Doe" --export docx
  
  # Search for exact phrase
  %(prog)s -d ./comments "deep web murder" -m phrase
  
  # Disable highlighting in terminal
  %(prog)s -d ./comments "murder" --no-highlight
  
  # Export to DOCX with highlighting
  %(prog)s -d ./comments "murder" --export docx
  
  # Only show comments with 10+ likes
  %(prog)s -d ./comments "murder" --min-likes 10
  
  # Disable auto-save
  %(prog)s -d ./comments "murder" --no-save
  
  # Show author statistics
  %(prog)s -d ./comments "murder" --stats
  
  # Search with regex pattern
  %(prog)s -d ./comments "murder(ed|ing|s)?" -m regex

Filename Patterns:
  Regular search:     {folder}_{timestamp}.json/docx
  User extraction:    user_{username}_{timestamp}.json/docx
  Most active users:  {folder}_most_active_top{N}_{timestamp}.json/docx
        """
    )
    
    parser.add_argument(
        'keywords',
        nargs='*',
        help='Keywords or phrases to search for (optional when using --most-active or --user without search)'
    )
    
    parser.add_argument(
        '-d', '--dir',
        required=True,
        help='Directory containing comment JSON files (REQUIRED)'
    )
    
    parser.add_argument(
        '--most-active',
        type=int,
        metavar='N',
        help='Show the N most active users (by comment count)'
    )
    
    parser.add_argument(
        '--user',
        type=str,
        metavar='USERNAME',
        help='Extract all comments from a specific user (exact username match)'
    )
    
    parser.add_argument(
        '-m', '--mode',
        choices=['any', 'all', 'phrase', 'regex'],
        default='any',
        help='Search mode: any=match any keyword, all=match all keywords, phrase=exact phrase, regex=regular expression (default: any)'
    )
    
    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='Enable case-sensitive search'
    )
    
    parser.add_argument(
        '--min-likes',
        type=int,
        default=0,
        help='Minimum number of likes (default: 0)'
    )
    
    parser.add_argument(
        '-n', '--max-results',
        type=int,
        default=None,
        help='Maximum number of results to display (default: all)'
    )
    
    parser.add_argument(
        '-s', '--sort',
        choices=['relevance', 'likes', 'date'],
        default='relevance',
        help='Sort results by: relevance, likes, or date (default: relevance)'
    )
    
    parser.add_argument(
        '--no-highlight',
        action='store_true',
        help='Disable keyword highlighting in terminal output'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Disable automatic saving of results'
    )
    
    parser.add_argument(
        '--export',
        nargs='+',
        choices=['json', 'docx'],
        default=['json'],
        help='Export formats: json, docx (default: json). Can specify multiple formats.'
    )
    
    parser.add_argument(
        '--no-docx-highlight',
        action='store_true',
        help='Disable keyword highlighting in DOCX export'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show author statistics'
    )
    
    return parser