"""Summary report for CampusFlow."""

from campusflow.sla import is_overdue, parse_iso
from campusflow.tickets import PRIORITIES, STATUSES, format_ticket


def build_report(tickets):
    """Return a dictionary with the total and the counts by status and priority."""
    # Start every count at 0, so a missing group still shows up as 0.
    by_status = {status: 0 for status in STATUSES}
    by_priority = {priority: 0 for priority in PRIORITIES}

    for ticket in tickets:
        if ticket["status"] not in by_status:
            raise ValueError(f"Ticket {ticket['id']} has an unknown status: {ticket['status']!r}")
        if ticket["priority"] not in by_priority:
            raise ValueError(f"Ticket {ticket['id']} has an unknown priority: {ticket['priority']!r}")
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1

    return {
        "total": len(tickets),
        "by_status": by_status,
        "by_priority": by_priority,
    }


def get_sla_attention_queue(tickets, now):
    """Return the unresolved tickets: overdue first, then earliest due_at, then lower ID.

    The tickets themselves are not changed, and the list is a new one.
    """
    unresolved = [ticket for ticket in tickets if ticket["status"] != "resolved"]
    return sorted(
        unresolved,
        key=lambda ticket: (
            not is_overdue(ticket, now),  # False sorts before True, so overdue comes first
            parse_iso(ticket["due_at"]),
            int(ticket["id"][1:]),
        ),
    )


def format_sla_ticket(ticket, now):
    """Return one queue line: an OVERDUE / on time label, the ticket and its deadline."""
    label = "[OVERDUE]" if is_overdue(ticket, now) else "[on time]"
    return f"{label} {format_ticket(ticket)} | due {ticket['due_at']}"


def build_metrics(tickets, now):
    """Return read-only counts. Every ticket is counted once in status and once in priority.

    "escalated_current_cycle" counts UNRESOLVED tickets that were escalated in
    their current SLA cycle (escalated_cycle equals escalation_cycle).
    """
    by_status = {status: 0 for status in STATUSES}
    by_priority = {priority: 0 for priority in PRIORITIES}
    overdue = 0
    escalated = 0

    for ticket in tickets:
        if ticket["status"] not in by_status:
            raise ValueError(f"Ticket {ticket['id']} has an unknown status: {ticket['status']!r}")
        if ticket["priority"] not in by_priority:
            raise ValueError(f"Ticket {ticket['id']} has an unknown priority: {ticket['priority']!r}")
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1
        if ticket["status"] != "resolved":
            if is_overdue(ticket, now):
                overdue += 1
            if ticket["escalated_cycle"] == ticket["escalation_cycle"]:
                escalated += 1

    return {
        "total": len(tickets),
        "open": by_status["open"],
        "in_progress": by_status["in_progress"],
        "resolved": by_status["resolved"],
        "overdue_unresolved": overdue,
        "escalated_current_cycle": escalated,
        "by_priority": by_priority,
    }
