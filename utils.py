import re
from datetime import datetime

def parse_views(view_str):
    """
    Convert Instagram view strings like '1.2M', '45K', '1,234' or '1.2M views' to integers.
    """
    if not view_str:
        return 0
    
    # Clean string: '1.2M views' -> '1.2M', '1,234 views' -> '1,234'
    # Also handle 'plays' and other common suffixes
    view_str = view_str.upper().replace(',', '').strip()
    view_str = re.sub(r'\s*(?:VIEWS|PLAYS|PLAY|VIEW).*$', '', view_str)
    
    # Handle cases like "1.2M" or "45K"
    multiplier = 1
    if 'M' in view_str:
        multiplier = 1_000_000
        view_str = view_str.replace('M', '')
    elif 'K' in view_str:
        multiplier = 1_000
        view_str = view_str.replace('K', '')
    elif 'B' in view_str:
        multiplier = 1_000_000_000
        view_str = view_str.replace('B', '')
    
    # Handle localized suffixes if any (e.g., "万" for 10k in some regions)
    if '万' in view_str:
        multiplier = 10_000
        view_str = view_str.replace('万', '')
    
    try:
        # Handle cases like '1.2' after removing 'M'
        # Use regex to extract the first number found
        num_match = re.search(r'(\d+\.?\d*)', view_str)
        if num_match:
            return int(float(num_match.group(1)) * multiplier)
        return 0
    except (ValueError, TypeError):
        return 0

def is_valid_reel_url(url):
    """
    Check if the provided URL is a valid Instagram reel URL.
    """
    pattern = r'^https?://(www\.)?instagram\.com/reels?/[\w-]+/?.*$'
    return bool(re.match(pattern, url))

def clean_username(username):
    """
    Clean username from potential extra characters.
    """
    if not username:
        return None
    return username.strip().replace('@', '')

def format_date(date_obj):
    """
    Format datetime object to string.
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    return str(date_obj)
