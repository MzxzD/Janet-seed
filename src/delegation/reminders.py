"""
Reminders delegation - "Hey Janet, add reminder to X" / "list my reminders"
EventKit Reminders integration. iOS App Intent performs the actual EventKit calls.
janet-seed receives reminder commands from iOS; the iOS app has calendar/reminders entitlement.
"""
from typing import List, Dict, Optional


def format_reminders_for_janet(reminders: List[Dict]) -> str:
    """
    Format reminders for Janet's response.
    
    Args:
        reminders: List of {"title", "due_date", "completed", "list_name"}
        
    Returns:
        Human-readable summary
    """
    if not reminders:
        return "No reminders."
    
    lines = []
    for r in reminders[:15]:
        title = r.get("title", "Untitled")
        due = r.get("due_date", "")
        done = r.get("completed", False)
        prefix = "[x] " if done else "[ ] "
        line = f"{prefix}{title}"
        if due:
            line += f" (due {due})"
        lines.append(line)
    if len(reminders) > 15:
        lines.append(f"... and {len(reminders) - 15} more")
    return "\n".join(lines)
