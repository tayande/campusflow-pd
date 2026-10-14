"""Time helpers for CampusFlow.

Every time in the program is an aware UTC datetime. Stored times are ISO-8601
text with an explicit offset, e.g. 2026-10-14T10:00:00+00:00.
"""

from datetime import datetime, timezone


def utc_now():
    """Return the current time as an aware UTC datetime (whole seconds).

    This is the only place that reads the real clock. Everything else is
    given `now` as an argument, so tests can use any time they like.
    """
    return datetime.now(timezone.utc).replace(microsecond=0)


def is_aware(moment):
    """Return True if this is a datetime that carries a timezone."""
    return isinstance(moment, datetime) and moment.utcoffset() is not None


def to_iso(moment):
    """Return an aware datetime as ISO-8601 text in UTC. Raise ValueError otherwise."""
    if not is_aware(moment):
        raise ValueError("Time must be a datetime with a timezone")
    return moment.astimezone(timezone.utc).isoformat()


def parse_iso(text):
    """Return an aware UTC datetime from ISO-8601 text. Raise ValueError if bad."""
    if not isinstance(text, str):
        raise ValueError(f"Time must be text, not {type(text).__name__}")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"Not a valid ISO-8601 time: {text!r}")
    if not is_aware(moment):
        raise ValueError(f"Time has no timezone: {text!r}")
    return moment.astimezone(timezone.utc)
