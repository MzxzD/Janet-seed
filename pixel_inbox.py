"""Shared pixel inbox for Pixel-to-Cursor relay (Courier persona)."""
import json
import os
import tempfile
import fcntl


PIXEL_INBOX_PATH = os.environ.get(
    "JANET_PIXEL_INBOX",
    os.path.join(tempfile.gettempdir(), "janet_pixel_inbox.json"),
)


def read_inbox():
    """Read pixel inbox from file."""
    if not os.path.exists(PIXEL_INBOX_PATH):
        return []
    try:
        with open(PIXEL_INBOX_PATH, "r") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (json.JSONDecodeError, IOError):
        return []


def append_inbox(entry: dict):
    """Append entry to pixel inbox."""
    entries = read_inbox()
    entries.append(entry)
    try:
        with open(PIXEL_INBOX_PATH, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(entries, f, indent=0)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except IOError as e:
        raise RuntimeError(f"Failed to write pixel inbox: {e}") from e


def pop_inbox():
    """Pop and return first entry from pixel inbox, or None."""
    entries = read_inbox()
    if not entries:
        return None
    popped = entries.pop(0)
    try:
        with open(PIXEL_INBOX_PATH, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(entries, f, indent=0)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except IOError as e:
        return None
    return popped
