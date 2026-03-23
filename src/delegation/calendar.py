"""
Calendar delegation - "Hey Janet, what's on my calendar today?"
Read-only EventKit integration. Requires iOS/macOS App to expose calendar data via API.
For janet-seed: receives calendar query requests from iOS; iOS App Intent fetches from EventKit.
"""
from typing import List, Dict, Optional
from datetime import datetime, date


def format_events_for_janet(events: List[Dict]) -> str:
    """
    Format calendar events for Janet's response.
    
    Args:
        events: List of {"title", "start", "end", "location", "all_day"}
        
    Returns:
        Human-readable summary
    """
    if not events:
        return "No events on your calendar for that period."
    
    lines = []
    for e in events[:10]:  # Max 10
        title = e.get("title", "Untitled")
        start = e.get("start", "")
        end = e.get("end", "")
        loc = e.get("location", "")
        all_day = e.get("all_day", False)
        if all_day:
            time_str = "All day"
        else:
            time_str = f"{start} - {end}" if end else str(start)
        line = f"• {title} ({time_str})"
        if loc:
            line += f" at {loc}"
        lines.append(line)
    if len(events) > 10:
        lines.append(f"... and {len(events) - 10} more")
    return "\n".join(lines)
