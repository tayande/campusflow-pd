"""Append-only event history for CampusFlow (the audit trail)."""

from datetime import datetime, timezone

EVENT_TYPES = ("CREATE", "ASSIGN", "START", "RESOLVE", "REOPEN", "ESCALATE")


def next_event_id(events):
    """Return the next ID: the highest existing number plus one, e.g. 'E004'."""
    highest = 0
    for event in events:
        number = int(event["event_id"][1:])
        if number > highest:
            highest = number
    return f"E{highest + 1:03d}"


def record_event(events, ticket_id, event_type, actor, now,
                 before_status, after_status, details=None):
    """Append one event to the list and return it.

    Call this only AFTER the operation has succeeded. Every check happens
    first, so a bad call leaves the events list untouched.
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Event type must be one of: {', '.join(EVENT_TYPES)}")
    if not isinstance(actor, str) or actor.strip() == "":
        raise ValueError("Actor cannot be blank")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Time must be a timezone-aware datetime")

    event = {
        "event_id": next_event_id(events),
        "ticket_id": ticket_id,
        "event_type": event_type,
        "actor": actor.strip(),
        "timestamp": now.astimezone(timezone.utc).isoformat(),
        "before_status": before_status,
        "after_status": after_status,
        "details": {} if details is None else dict(details),
    }
    events.append(event)
    return event

def get_history(events, ticket_id):
    """Return this ticket's events, oldest first. The events list is not changed.

    Events with the same timestamp are ordered by their numeric event ID.
    """
    wanted = ticket_id.strip().upper()
    mine = [event for event in events if event["ticket_id"] == wanted]
    return sorted(
        mine,
        key=lambda event: (
            datetime.fromisoformat(event["timestamp"]),
            int(event["event_id"][1:]),
        ),
    )


def format_event(event):
    """Return one event as a single readable line for the menu to print."""
    before = event["before_status"] or "-"
    after = event["after_status"] or "-"
    details = ", ".join(f"{key}={value}" for key, value in event["details"].items()) or "-"
    return (
        f"{event['event_id']} | {event['timestamp']} | {event['event_type']} | "
        f"{event['actor']} | {before} -> {after} | {details}"
    )