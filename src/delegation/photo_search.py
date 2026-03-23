"""
Photo search delegation - "Hey Janet, find photos of X"
Natural language search. iOS uses Photos framework + PHFetchResult.
janet-seed receives photo search requests; iOS App performs the actual search.
"""
from typing import List, Dict, Optional


def format_photo_results(photos: List[Dict]) -> str:
    """
    Format photo search results for Janet's response.
    
    Args:
        photos: List of {"local_id", "date", "count"}
        
    Returns:
        Human-readable summary
    """
    if not photos:
        return "No photos found."
    if len(photos) == 1:
        return f"Found 1 photo."
    return f"Found {len(photos)} photos."
