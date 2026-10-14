"""Service-level deadlines (SLA) for CampusFlow.

A ticket has a deadline, `due_at`, that depends on its priority. The deadline
runs from the start of the ticket's current cycle: its creation time at first,
and the reopen time after a reopen.
"""

from datetime import timedelta

from campusflow.timeutil import is_aware, parse_iso, to_iso, utc_now  # noqa: F401

# Minutes allowed before a ticket of each priority is overdue.
SLA_MINUTES = {
    "critical": 60,
    "high": 240,
    "medium": 1440,
    "low": 2880,
}


def calculate_due_at(priority, cycle_start):
    """Return the deadline (an aware datetime) for a ticket of this priority."""
    if priority not in SLA_MINUTES:
        raise ValueError(f"Unknown priority: {priority!r}")
    if not is_aware(cycle_start):
        raise ValueError("Cycle start must be a datetime with a timezone")
    return cycle_start + timedelta(minutes=SLA_MINUTES[priority])


def is_overdue(ticket, now):
    """Return True if the ticket is unresolved and `now` is strictly after its deadline."""
    if not is_aware(now):
        raise ValueError("Now must be a datetime with a timezone")
    if ticket["status"] == "resolved":
        return False
    return now > parse_iso(ticket["due_at"])
