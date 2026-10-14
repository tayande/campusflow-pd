
"""Service-level deadlines (SLA) for CampusFlow.

A ticket has a deadline, `due_at`, that depends on its priority. The deadline
runs from the start of the ticket's current cycle: its creation time at first,
and the reopen time after a reopen.
"""

from datetime import timedelta

from campusflow.history import record_event
from campusflow.timeutil import is_aware, parse_iso, to_iso, utc_now  # noqa: F401

# Minutes allowed before a ticket of each priority is overdue.
SLA_MINUTES = {
    "critical": 60,
    "high": 240,
    "medium": 1440,
    "low": 2880,
}


def calculate_due_at(priority, cycle_start):
    """Return the deadline (an aware datetime) for this ticket's priority."""
    if priority not in SLA_MINUTES:
        raise ValueError(f"Unknown priority: {priority!r}")
    if not is_aware(cycle_start):
        raise ValueError("Cycle start must be a datetime with a timezone")
    return cycle_start + timedelta(minutes=SLA_MINUTES[priority])


def is_overdue(ticket, now):
    """Return True if the ticket is unresolved and now is strictly after its deadline."""
    if not is_aware(now):
        raise ValueError("Now must be a datetime with a timezone")
    if ticket["status"] == "resolved":
        return False
    return now > parse_iso(ticket["due_at"])


def escalate_overdue(tickets, events, now, actor):
    """Record one ESCALATE event per overdue ticket in its current cycle.

    A ticket counts as escalated in its current cycle when
    escalated_cycle == escalation_cycle. Reopening increments escalation_cycle,
    allowing the ticket to be escalated again in the new cycle.

    Repeated checks in the same cycle do not create duplicate events.
    Escalation does not change the ticket's assignment, priority, or status.

    Returns:
        A dictionary containing newly_escalated and already_escalated counts.
    """
    if not is_aware(now):
        raise ValueError("Now must be a datetime with a timezone")
    if not isinstance(actor, str) or actor.strip() == "":
        raise ValueError("Actor cannot be blank")

    newly = 0
    already = 0

    for ticket in tickets:
        if not is_overdue(ticket, now):
            continue

        cycle = ticket.get("escalation_cycle", 0)

        if ticket.get("escalated_cycle") == cycle:
            already += 1
            continue

        # Record the event before updating the ticket's escalation marker.
        record_event(
            events,
            ticket["id"],
            "ESCALATE",
            actor,
            now,
            ticket["status"],
            ticket["status"],
            {"cycle": cycle, "due_at": ticket["due_at"]},
        )

        ticket["escalated_cycle"] = cycle
        ticket["updated_at"] = to_iso(now)
        newly += 1

    return {
        "newly_escalated": newly,
        "already_escalated": already,
    }
