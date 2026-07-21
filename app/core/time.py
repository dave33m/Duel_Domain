from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC datetime, for consistent comparison against SQLite-stored timestamps."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
